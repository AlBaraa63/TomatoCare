"""A6 — Stage 2 fine-tuning: top of the MobileNetV3-Large base.

Loads Stage 1's best checkpoint, unfreezes the last 30 layers of the base
model, and continues training with a much lower learning rate (1e-4 vs
1e-3). Lower LR is critical: fine-tuning at Stage 1's LR would destroy
the ImageNet representations in the bottom layers that we *don't* want
to retrain.

Outputs:
  - ml/models/checkpoints/stage2_best.keras
  - ml/results/results_stage2.json

Caching: skips if stage2_best.keras exists.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402
from train_stage1 import compute_class_weights  # noqa: E402


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


def main() -> None:
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset, build_train_dataset
    from utils.model_factory import build_model, unfreeze_top_layers

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    banner_script("A6 Stage 2 Fine-Tuning", device)

    config = load_config()
    root = project_root()
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    results_dir = root / config["paths"]["results_dir"]

    stage1_ckpt = ckpt_dir / "stage1_best.keras"
    stage2_ckpt = ckpt_dir / "stage2_best.keras"
    results_path = results_dir / "results_stage2.json"

    if not stage1_ckpt.exists():
        raise FileNotFoundError(
            f"{stage1_ckpt} not found. Run train_stage1.py first."
        )

    if stage2_ckpt.exists() and results_path.exists():
        print(f"  >> SKIP: {stage2_ckpt} already exists. Delete to re-run.")
        with open(results_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    banner_phase("Loading Stage 1 Checkpoint")
    # Build a fresh model using the fixed factory (base(x) — no training=False),
    # then transfer weights from the Stage 1 checkpoint by value.
    # We cannot use load_model() here: it restores the full saved graph which
    # has training=False baked in, causing FusedBatchNormGradV3 to fail during
    # Stage 2 backprop through the unfrozen top BN layers.
    _loaded = tf.keras.models.load_model(str(stage1_ckpt))
    model = build_model(
        num_classes=len(config["classes"]),
        img_size=config["img_size"],
        dropout_rate=config["dropout_rate"],
    )
    model.set_weights(_loaded.get_weights())
    del _loaded
    banner_step("CK-01", "Stage 1 best weights loaded",
                path=str(stage1_ckpt))

    banner_phase("Building Datasets")
    augmented_train_dir = root / config["paths"]["augmented_dir"] / "train"
    train_ds = build_train_dataset(augmented_train_dir, config)
    val_ds = build_split_dataset(
        root / config["paths"]["splits_dir"] / "val.csv", config)

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

    banner_phase("Unfreezing Top Layers")
    unfreeze_top_layers(model, config["fine_tune_from_layer"])
    # Re-compile with the lower Stage 2 LR — required because optimizer
    # state from Stage 1 is at the higher LR and would overshoot.
    label_smoothing = float((config.get("loss") or {}).get("label_smoothing", 0.0))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config["stage2_lr"]),
        loss=tf.keras.losses.CategoricalCrossentropy(
            label_smoothing=label_smoothing),
        metrics=["accuracy"],
    )
    trainable = sum(
        tf.keras.backend.count_params(w) for w in model.trainable_weights
    )
    banner_step("M-02", f"Unfroze last {abs(config['fine_tune_from_layer'])} layers",
                trainable_params=int(trainable),
                stage2_lr=config["stage2_lr"],
                label_smoothing=label_smoothing)

    banner_phase("Stage 2 Training — Fine-Tune")
    # Tighter patience than Stage 1 — fine-tuning overfits fast.
    stage2_patience = int(config.get("stage2_patience",
                                     config["stage1_patience"]))
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            mode="min",
            patience=stage2_patience,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(stage2_ckpt),
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1,
        ),
    ]

    class StepBanner(tf.keras.callbacks.Callback):
        def on_epoch_begin(self, epoch, logs=None):
            self._t0 = time.time()
        def on_epoch_end(self, epoch, logs=None):
            logs = logs or {}
            if (epoch + 1) % 5 == 0 or epoch == 0:
                banner_step(
                    f"E-{epoch+1:03d}",
                    f"Epoch {epoch+1}/{config['stage2_epochs']}",
                    train_loss=f"{logs.get('loss', 0):.4f}",
                    val_accuracy=f"{logs.get('val_accuracy', 0)*100:.2f}%",
                    time_s=f"{time.time()-self._t0:.1f}s",
                )
    callbacks.append(StepBanner())

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["stage2_epochs"],
        callbacks=callbacks,
        class_weight=class_weight,
        verbose=2,
    )

    h = {k: [float(x) for x in v] for k, v in history.history.items()}
    val_losses = h.get("val_loss", [])
    best_idx = int(np.argmin(val_losses)) if val_losses else 0
    best_val_acc = float(h.get("val_accuracy", [0.0])[best_idx]) \
        if h.get("val_accuracy") else 0.0
    best_val_loss = float(val_losses[best_idx]) if val_losses else 0.0
    report = {
        "best_val_loss": best_val_loss,
        "best_val_accuracy": best_val_acc,
        "best_epoch": best_idx + 1,
        "total_epochs_run": len(h.get("loss", [])),
        "stage2_lr": float(config["stage2_lr"]),
        "stage2_patience": stage2_patience,
        "label_smoothing": label_smoothing,
        "fine_tuned_from_layer": int(config["fine_tune_from_layer"]),
        "class_weights": {str(k): float(v) for k, v in class_weight.items()},
        "history": h,
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-02", "Stage 2 report saved",
                best_val_accuracy=f"{best_val_acc*100:.2f}%",
                best_val_loss=f"{best_val_loss:.4f}",
                path=str(results_path))
    print(f"  >> Saved to : {stage2_ckpt}")


if __name__ == "__main__":
    main()
