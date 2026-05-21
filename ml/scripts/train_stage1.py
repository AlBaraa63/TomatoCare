"""A5 — Stage 1 training: classification head only.

Base model is frozen. Only the GAP + Dropout + Dense(num_classes) head
trains. This learns to map MobileNetV3's ImageNet features onto our 11
classes (10 tomato disease + Tomato_NotALeaf) without disturbing the
pretrained representations. Stage 2 (separate script) then fine-tunes
the top of the base model with a much lower LR.

Class weights ('balanced' mode by default) compensate for the fact that
the Tomato_NotALeaf class — sourced from imagenette — is ~3x larger than
each per-tomato class and would otherwise bias the model toward rejecting
inputs. Label smoothing (default 0.05) gently de-confidences the model
so the 0.60 threshold on the Android side maps to meaningful probability.

Outputs:
  - ml/models/checkpoints/stage1_best.keras   (best-val-loss weights)
  - ml/results/results_stage1.json            (history + best metrics)

Caching: if stage1_best.keras already exists, the script loads it and
exits without retraining. Delete the checkpoint to force a re-run.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

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


def compute_class_weights(augmented_train_dir: Path,
                          classes: list[str],
                          mode: str = "balanced",
                          manual: dict | None = None) -> dict[int, float]:
    """Return {class_index: weight} from the actual augmented training set.

    'balanced' mirrors sklearn's compute_class_weight: n_samples / (n_classes * count_c).
    The augmented folder is the ground truth for what the model will see —
    counting train.csv would miss the 4x augmentation multiplier.
    """
    if mode == "none":
        return {i: 1.0 for i in range(len(classes))}
    if mode == "manual":
        if not manual:
            raise ValueError("class_weights.mode='manual' but manual_weights missing")
        return {int(k): float(v) for k, v in manual.items()}
    # balanced
    counts: dict[int, int] = {}
    total = 0
    for idx, cls in enumerate(classes):
        cls_dir = augmented_train_dir / cls
        if cls_dir.exists():
            n = sum(1 for p in cls_dir.iterdir() if p.is_file())
        else:
            n = 0
        counts[idx] = n
        total += n
    n_classes = len(classes)
    weights: dict[int, float] = {}
    for idx in range(n_classes):
        c = max(counts[idx], 1)
        weights[idx] = total / (n_classes * c)
    return weights


def main() -> None:
    # set_seed must run before TF imports anything that uses RNG.
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset, build_train_dataset
    from utils.model_factory import build_model

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    banner_script("A5 Stage 1 Training (head only)", device)

    config = load_config()
    root = project_root()
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    results_dir = root / config["paths"]["results_dir"]
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    ckpt_path = ckpt_dir / "stage1_best.keras"
    results_path = results_dir / "results_stage1.json"

    if ckpt_path.exists() and results_path.exists():
        print(f"  >> SKIP: {ckpt_path} already exists. Delete to re-run.")
        with open(results_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    banner_phase("Building Datasets")
    augmented_train_dir = root / config["paths"]["augmented_dir"] / "train"
    train_ds = build_train_dataset(augmented_train_dir, config)
    val_ds = build_split_dataset(
        root / config["paths"]["splits_dir"] / "val.csv", config)
    banner_step("DS-01", "Datasets built",
                batch_size=config["batch_size"], img_size=config["img_size"])

    banner_phase("Computing Class Weights")
    cw_cfg = config.get("class_weights") or {}
    class_weight = compute_class_weights(
        augmented_train_dir, config["classes"],
        mode=cw_cfg.get("mode", "balanced"),
        manual=cw_cfg.get("manual_weights"),
    )
    for idx, cls in enumerate(config["classes"]):
        banner_step(f"CW-{idx:02d}", cls,
                    weight=f"{class_weight[idx]:.3f}")

    banner_phase("Building Model")
    model = build_model(num_classes=len(config["classes"]),
                        img_size=config["img_size"],
                        dropout_rate=config["dropout_rate"])
    label_smoothing = float((config.get("loss") or {}).get("label_smoothing", 0.0))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config["stage1_lr"]),
        loss=tf.keras.losses.CategoricalCrossentropy(
            label_smoothing=label_smoothing),
        metrics=["accuracy"],
    )
    trainable = sum(
        tf.keras.backend.count_params(w) for w in model.trainable_weights
    )
    total = model.count_params()
    banner_step("M-01", "MobileNetV3-Large frozen + Dense head",
                trainable_params=int(trainable), total_params=int(total),
                num_classes=len(config["classes"]),
                label_smoothing=label_smoothing)

    banner_phase("Stage 1 Training — Head Only")
    # Monitor val_loss (not val_accuracy): label smoothing + class weights
    # decorrelate accuracy from loss; loss is the truer convergence signal.
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            mode="min",
            patience=config["stage1_patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(ckpt_path),
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1,
        ),
    ]

    class StepBanner(tf.keras.callbacks.Callback):
        # Per spec: print a Level-3 banner every 5 epochs.
        def on_epoch_begin(self, epoch, logs=None):
            self._t0 = time.time()
        def on_epoch_end(self, epoch, logs=None):
            logs = logs or {}
            if (epoch + 1) % 5 == 0 or epoch == 0:
                banner_step(
                    f"E-{epoch+1:03d}",
                    f"Epoch {epoch+1}/{config['stage1_epochs']}",
                    train_loss=f"{logs.get('loss', 0):.4f}",
                    val_accuracy=f"{logs.get('val_accuracy', 0)*100:.2f}%",
                    time_s=f"{time.time()-self._t0:.1f}s",
                )
    callbacks.append(StepBanner())

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["stage1_epochs"],
        callbacks=callbacks,
        class_weight=class_weight,
        verbose=2,
    )

    h = {k: [float(x) for x in v] for k, v in history.history.items()}
    val_losses = h.get("val_loss", [])
    if val_losses:
        best_idx = int(np.argmin(val_losses))
    else:
        best_idx = 0
    best_val_acc = float(h.get("val_accuracy", [0.0])[best_idx]) \
        if h.get("val_accuracy") else 0.0
    best_val_loss = float(val_losses[best_idx]) if val_losses else 0.0
    report = {
        "best_val_loss": best_val_loss,
        "best_val_accuracy": best_val_acc,
        "best_epoch": best_idx + 1,
        "total_epochs_run": len(h.get("loss", [])),
        "stage1_lr": float(config["stage1_lr"]),
        "label_smoothing": label_smoothing,
        "class_weights": {str(k): float(v) for k, v in class_weight.items()},
        "history": h,
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Stage 1 report saved",
                best_val_accuracy=f"{best_val_acc*100:.2f}%",
                best_val_loss=f"{best_val_loss:.4f}",
                path=str(results_path))
    print(f"  >> Saved to : {ckpt_path}")


if __name__ == "__main__":
    main()
