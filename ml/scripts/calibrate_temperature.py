"""A6.5 — Post-hoc temperature scaling calibration.

Loads stage2_best.keras, collects pre-softmax logits on the val set, fits
a single scalar temperature T that minimises NLL of the softmax(logits/T)
distribution, then re-saves the model with T baked in as a Lambda layer
between the Dense and softmax. The Android side needs zero changes — the
calibrated .tflite still has shape [1, num_classes] and still outputs
softmax probabilities; they're just better calibrated.

Why temperature scaling and not Platt scaling / isotonic / etc:
  - Temperature is a single parameter — provably won't change argmax, so
    classification accuracy is preserved exactly. Multi-parameter methods
    can rerank classes and erode the accuracy we worked to earn.
  - It's the standard for deep classifiers (Guo et al, "On Calibration of
    Modern Neural Networks", 2017).

Why "baked in" rather than applied at inference on Android:
  - One place to store T (the model file itself), so Android can't get out
    of sync. Bumping model_version forces a rebuild; T travels with it.
  - The TFLite converter walks the Keras graph, so the Lambda(x/T) layer
    becomes a single DIV op — no runtime overhead worth measuring.

Outputs:
  - ml/models/checkpoints/stage2_calibrated.keras
  - ml/results/calibration.json    (T, NLL before/after, ECE before/after)
  - ml/results/reliability_diagram.png

Caching: skips if stage2_calibrated.keras already exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402


def banner_script(purpose: str, device: str) -> None:
    print("##############################################################")
    print(f"  TomatoCare — {purpose}")
    print(f"  Device : {device}")
    print(f"  Seed   : 42")
    print("##############################################################")


def banner_phase(name: str) -> None:
    print("==============================================================")
    print(f"  PHASE: {name}")
    print("==============================================================")


def banner_step(step_id: str, desc: str, **params) -> None:
    print("--------------------------------------------------------------")
    print(f"  [{step_id}] {desc}")
    if params:
        print("  " + "  |  ".join(f"{k}: {v}" for k, v in params.items()))
    print("--------------------------------------------------------------")


def _softmax_np(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def _nll(logits: np.ndarray, labels: np.ndarray, T: float) -> float:
    """Mean negative log-likelihood of softmax(logits/T) at the true class."""
    probs = _softmax_np(logits / T)
    # Clip to avoid log(0); the math is identical for any clip << 1.
    probs = np.clip(probs, 1e-12, 1.0)
    return float(-np.log(probs[np.arange(len(labels)), labels]).mean())


def _ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    """Expected Calibration Error.

    Bin predictions by their argmax-confidence and compare bin accuracy to
    bin mean confidence. Lower is better; a perfectly calibrated model
    would score 0.
    """
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == labels).astype(np.float32)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(labels)
    for i in range(n_bins):
        in_bin = (conf > bins[i]) & (conf <= bins[i + 1])
        if not in_bin.any():
            continue
        bin_conf = conf[in_bin].mean()
        bin_acc = correct[in_bin].mean()
        ece += (in_bin.sum() / n) * abs(bin_conf - bin_acc)
    return float(ece)


def _fit_temperature(logits: np.ndarray, labels: np.ndarray,
                     max_iter: int = 50) -> float:
    """Fit T via scipy LBFGS. T is constrained > 0 via parameterisation."""
    from scipy.optimize import minimize

    def objective(log_T: float) -> float:
        # Optimise log(T) so T stays strictly positive.
        T = float(np.exp(log_T))
        return _nll(logits, labels, T)

    result = minimize(
        objective, x0=np.array([0.0]),  # T=1 to start
        method="L-BFGS-B",
        options={"maxiter": max_iter, "disp": False},
    )
    return float(np.exp(result.x[0]))


def _build_logits_model(softmax_model):
    """Take a Keras model whose final layer has softmax activation, return a
    NEW model that outputs the pre-softmax logits.

    We do this by temporarily setting the final Dense's activation to linear,
    re-tracing the graph, and reading the resulting tensor. The original model
    is left untouched.
    """
    import tensorflow as tf
    # Locate the predictions Dense layer.
    pred_layer = None
    for layer in reversed(softmax_model.layers):
        if isinstance(layer, tf.keras.layers.Dense):
            pred_layer = layer
            break
    if pred_layer is None:
        raise RuntimeError("Could not find the Dense prediction layer.")

    # Clone the model, then swap the activation on the cloned final Dense.
    # tf.keras.models.clone_model preserves architecture but not weights.
    cloned = tf.keras.models.clone_model(softmax_model)
    cloned.set_weights(softmax_model.get_weights())
    cloned_pred = None
    for layer in reversed(cloned.layers):
        if isinstance(layer, tf.keras.layers.Dense):
            cloned_pred = layer
            break
    if cloned_pred is None:
        raise RuntimeError("Clone has no Dense final layer.")
    cloned_pred.activation = tf.keras.activations.linear
    # Force the model to recompile its forward function with new activation.
    logits_model = tf.keras.models.Model(
        inputs=cloned.inputs, outputs=cloned_pred.output, name="TomatoCare_logits")
    return logits_model


def _build_calibrated_model(softmax_model, T: float):
    """Build a NEW Keras model: backbone+head → /T → softmax. Same shape.

    We construct it by reusing the softmax_model's input and reading the
    pre-softmax tensor (obtained as in _build_logits_model), then appending
    TemperatureScale(T) → softmax. Weights are preserved 1:1 from softmax_model.
    Uses a proper Keras Layer (not Lambda) so the saved .keras file deserialises
    cleanly in eval_model.py and export_tflite.py.
    """
    import tensorflow as tf
    from utils.layers import get_temperature_scale_layer
    TemperatureScale = get_temperature_scale_layer()
    logits_model = _build_logits_model(softmax_model)
    inputs = logits_model.inputs[0]
    logits = logits_model(inputs)
    scaled = TemperatureScale(temperature=T, name="temperature_scale")(logits)
    probs = tf.keras.layers.Softmax(name="predictions_calibrated")(scaled)
    return tf.keras.models.Model(
        inputs=inputs, outputs=probs, name="TomatoCare_calibrated")


def main() -> None:
    set_seed(42)
    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    banner_script("A6.5 Temperature Scaling Calibration", device)

    config = load_config()
    if not (config.get("calibration") or {}).get("enabled", False):
        print("  >> calibration.enabled=false in config; skipping.")
        return

    root = project_root()
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    results_dir = root / config["paths"]["results_dir"]
    src_path = ckpt_dir / "stage2_best.keras"
    dst_path = ckpt_dir / "stage2_calibrated.keras"
    cal_path = results_dir / "calibration.json"
    diag_path = results_dir / "reliability_diagram.png"

    if not src_path.exists():
        raise FileNotFoundError(
            f"{src_path} not found. Run train_stage2.py first."
        )
    if dst_path.exists() and cal_path.exists():
        print(f"  >> SKIP: {dst_path} exists. Delete to re-run.")
        with open(cal_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    banner_phase("Loading Stage 2 Model + Val Set")
    softmax_model = tf.keras.models.load_model(src_path)
    val_csv = root / config["paths"]["splits_dir"] / "val.csv"
    val_ds = build_split_dataset(val_csv, config)
    banner_step("LD-01", "Loaded",
                model=str(src_path), val_csv=str(val_csv))

    banner_phase("Collecting Pre-Softmax Logits on Val")
    logits_model = _build_logits_model(softmax_model)
    all_logits: list[np.ndarray] = []
    all_labels: list[int] = []
    for batch_x, batch_y in val_ds:
        z = logits_model.predict(batch_x, verbose=0)
        all_logits.append(z)
        all_labels.extend(np.argmax(batch_y.numpy(), axis=1).tolist())
    logits = np.concatenate(all_logits, axis=0)
    labels = np.asarray(all_labels, dtype=np.int64)
    banner_step("LG-01", "Logits collected",
                n_samples=len(labels), n_classes=logits.shape[1])

    banner_phase("Computing Pre-Calibration Metrics")
    probs_pre = _softmax_np(logits)
    nll_pre = _nll(logits, labels, T=1.0)
    ece_pre = _ece(probs_pre, labels)
    banner_step("M-PRE", "Pre-calibration", nll=f"{nll_pre:.4f}",
                ece=f"{ece_pre:.4f}")

    banner_phase("Fitting Temperature (LBFGS)")
    max_iter = int((config.get("calibration") or {}).get("max_iter", 50))
    T = _fit_temperature(logits, labels, max_iter=max_iter)
    banner_step("FIT-01", "Temperature found", T=f"{T:.4f}",
                interpretation="T>1 means model was overconfident" if T > 1.0
                else "T<1 means model was underconfident")

    banner_phase("Computing Post-Calibration Metrics")
    probs_post = _softmax_np(logits / T)
    nll_post = _nll(logits, labels, T=T)
    ece_post = _ece(probs_post, labels)
    banner_step("M-POST", "Post-calibration", nll=f"{nll_post:.4f}",
                ece=f"{ece_post:.4f}",
                ece_improvement=f"{(ece_pre - ece_post):+.4f}")

    banner_phase("Reliability Diagram")
    n_bins = 15
    conf_post = probs_post.max(axis=1)
    pred_post = probs_post.argmax(axis=1)
    correct = (pred_post == labels).astype(np.float32)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    bin_acc = np.zeros(n_bins)
    bin_conf = np.zeros(n_bins)
    bin_count = np.zeros(n_bins)
    for i in range(n_bins):
        in_bin = (conf_post > bins[i]) & (conf_post <= bins[i + 1])
        if in_bin.any():
            bin_acc[i] = correct[in_bin].mean()
            bin_conf[i] = conf_post[in_bin].mean()
            bin_count[i] = in_bin.sum()
    plt.figure(figsize=(7, 7))
    plt.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    plt.bar(bin_centers, bin_acc, width=1.0 / n_bins, edgecolor="black",
            alpha=0.7, label="Bin accuracy")
    plt.plot(bin_centers, bin_conf, "ro-", label="Bin mean confidence")
    plt.xlabel("Confidence (max softmax)")
    plt.ylabel("Accuracy")
    plt.title(f"Reliability Diagram (T={T:.3f}, ECE={ece_post:.4f})")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(diag_path, dpi=120)
    plt.close()
    banner_step("RD-01", "Reliability diagram saved", path=str(diag_path))

    banner_phase("Baking T into Calibrated Model")
    calibrated = _build_calibrated_model(softmax_model, T)
    # Smoke test — output shape must equal softmax_model's output shape and
    # argmax must be invariant to T (sanity check that scaling didn't break anything).
    sample = next(iter(val_ds))[0]
    pre = softmax_model.predict(sample, verbose=0)
    post = calibrated.predict(sample, verbose=0)
    if pre.shape != post.shape:
        raise RuntimeError(
            f"Calibrated output shape {post.shape} != original {pre.shape}")
    same_argmax = (np.argmax(pre, axis=1) == np.argmax(post, axis=1)).mean()
    banner_step("CHK-01", "Sanity check (argmax must be invariant)",
                argmax_match=f"{same_argmax*100:.2f}%",
                shape=str(post.shape))
    if same_argmax < 1.0:
        raise RuntimeError(
            "Argmax changed after temperature scaling — this should be "
            "mathematically impossible. Check that the Lambda layer was "
            "inserted before softmax, not after."
        )

    calibrated.save(dst_path)
    banner_step("SAVE-01", "Calibrated model saved", path=str(dst_path))

    report = {
        "temperature": float(T),
        "nll_pre": float(nll_pre),
        "nll_post": float(nll_post),
        "ece_pre": float(ece_pre),
        "ece_post": float(ece_post),
        "ece_improvement": float(ece_pre - ece_post),
        "n_val_samples": int(len(labels)),
        "source_checkpoint": str(src_path),
        "calibrated_checkpoint": str(dst_path),
    }
    with open(cal_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Calibration report saved", path=str(cal_path))


if __name__ == "__main__":
    main()
