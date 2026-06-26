"""TomatoCare — Post-hoc Temperature Scaling Calibration
Fits a single scaling factor T to validation logits to align prediction confidence
with real-world accuracies. T is saved inside the final Keras model division layer.
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





# Standard softmax helper to convert raw scores (logits) into probability percentages
def _softmax_np(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


# Calculates the prediction loss (Negative Log Likelihood). We want to minimize this.
def _nll(logits: np.ndarray, labels: np.ndarray, T: float) -> float:
    """Mean negative log-likelihood of softmax(logits/T) at the true class."""
    probs = _softmax_np(logits / T)
    # Clip to avoid log(0); the math is identical for any clip << 1.
    probs = np.clip(probs, 1e-12, 1.0)
    return float(-np.log(probs[np.arange(len(labels)), labels]).mean())


# Expected Calibration Error helper to measure how well confidence matches accuracy
def _ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
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


# Runs optimization using L-BFGS to find the best temperature scalar T
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


# Temporarily changes the final model layer's activation from Softmax to Linear
# to extract the raw, un-scaled scores (logits) from the network
def _build_logits_model(softmax_model):
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


# Constructs the final calibrated model by inserting our custom TemperatureScale 
# layer directly before the final Softmax activation layer
def _build_calibrated_model(softmax_model, T: float):
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
    print(f"--- TomatoCare — Temperature Scaling Calibration ({device}) ---")

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
            f"{src_path} not found. Run step2_train_stage2.py first."
        )
    if dst_path.exists() and cal_path.exists():
        print(f"  >> SKIP: {dst_path} exists. Delete to re-run.")
        with open(cal_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    print("--- Loading Stage 2 Model + Val Set ---")
    # STEP 1: Load the Stage 2 fine-tuned model and validation dataset
    softmax_model = tf.keras.models.load_model(src_path)
    val_csv = root / config["paths"]["splits_dir"] / "val.csv"
    val_ds = build_split_dataset(val_csv, config)
    print(f"Loaded model from: {src_path} | Val CSV: {val_csv}")

    print("--- Collecting Pre-Softmax Logits on Val ---")
    # STEP 2: Swap the final activation from Softmax to Linear to extract "logits" (raw scores)
    logits_model = _build_logits_model(softmax_model)
    all_logits: list[np.ndarray] = []
    all_labels: list[int] = []
    for batch_x, batch_y in val_ds:
        z = logits_model.predict(batch_x, verbose=0)
        all_logits.append(z)
        all_labels.extend(np.argmax(batch_y.numpy(), axis=1).tolist())
    logits = np.concatenate(all_logits, axis=0)
    labels = np.asarray(all_labels, dtype=np.int64)
    print(f"Logits collected: {len(labels)} samples, {logits.shape[1]} classes")

    print("--- Computing Pre-Calibration Metrics ---")
    # STEP 3: Compute initial calibration error (ECE) before applying temperature scaling
    probs_pre = _softmax_np(logits)
    nll_pre = _nll(logits, labels, T=1.0)
    ece_pre = _ece(probs_pre, labels)
    print(f"Pre-calibration: NLL={nll_pre:.4f}, ECE={ece_pre:.4f}")

    print("--- Fitting Temperature (LBFGS) ---")
    # STEP 4: Run optimization (L-BFGS) to find the scaling factor T that minimizes validation loss (NLL)
    max_iter = int((config.get("calibration") or {}).get("max_iter", 50))
    T = _fit_temperature(logits, labels, max_iter=max_iter)
    print(f"Temperature T found: {T:.4f}")

    print("--- Computing Post-Calibration Metrics ---")
    # STEP 5: Re-evaluate calibration error (ECE) with the optimized Temperature factor T
    probs_post = _softmax_np(logits / T)
    nll_post = _nll(logits, labels, T=T)
    ece_post = _ece(probs_post, labels)
    print(f"Post-calibration: NLL={nll_post:.4f}, ECE={ece_post:.4f} (ECE improvement: {(ece_pre - ece_post):+.4f})")

    print("--- Saving Reliability Diagram ---")
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
    print(f"Reliability diagram saved to: {diag_path}")

    print("--- Baking T into Calibrated Model ---")
    # STEP 6: Insert a custom division layer `/ T` right before the final Softmax layer.
    # EXPLANATION FOR PRESENTATION: We divide the model's raw visual scores by our calibrated temperature T. 
    # This adjusts the confidence scores to be realistic without changing the actual disease prediction. 
    # By inserting it directly inside the model graph, the Android app automatically gets calibrated confidence scores.
    calibrated = _build_calibrated_model(softmax_model, T)
    
    # STEP 7: Sanity check to confirm temperature scaling did not alter the classification predictions (argmax)
    sample = next(iter(val_ds))[0]
    pre = softmax_model.predict(sample, verbose=0)
    post = calibrated.predict(sample, verbose=0)
    if pre.shape != post.shape:
        raise RuntimeError(
            f"Calibrated output shape {post.shape} != original {pre.shape}")
    same_argmax = (np.argmax(pre, axis=1) == np.argmax(post, axis=1)).mean()
    print(f"Sanity check: argmax match = {same_argmax*100:.2f}% | output shape = {post.shape}")
    if same_argmax < 1.0:
        raise RuntimeError(
            "Argmax changed after temperature scaling — this should be "
            "mathematically impossible. Check that the Lambda layer was "
            "inserted before softmax, not after."
        )

    # STEP 8: Save the calibrated Keras model file (.keras)
    calibrated.save(dst_path)
    print(f"Calibrated model saved to: {dst_path}")

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
    print(f"Calibration report saved to: {cal_path}")


if __name__ == "__main__":
    main()
