"""A5 — Stage 1 training: classification head only.

Base model is frozen. Only the GAP + Dropout + Dense(10) head trains.
This learns to map MobileNetV3's ImageNet features onto our 10 disease
classes without disturbing the pretrained representations. Stage 2
(separate script) then fine-tunes the top of the base model with a much
lower LR.

Outputs:
  - ml/models/checkpoints/stage1_best.keras   (best-val-acc weights)
  - ml/results/results_stage1.json            (history + best metrics)

Caching: if stage1_best.keras already exists, the script loads it and
exits without retraining. Delete the checkpoint to force a re-run.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

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
    train_ds = build_train_dataset(
        root / config["paths"]["augmented_dir"] / "train", config)
    val_ds = build_split_dataset(
        root / config["paths"]["splits_dir"] / "val.csv", config)
    banner_step("DS-01", "Datasets built",
                batch_size=config["batch_size"], img_size=config["img_size"])

    banner_phase("Building Model")
    model = build_model(num_classes=len(config["classes"]),
                        img_size=config["img_size"],
                        dropout_rate=config["dropout_rate"])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config["stage1_lr"]),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    trainable = sum(
        tf.keras.backend.count_params(w) for w in model.trainable_weights
    )
    total = model.count_params()
    banner_step("M-01", "MobileNetV3-Large frozen + Dense head",
                trainable_params=int(trainable), total_params=int(total))

    banner_phase("Stage 1 Training — Head Only")
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=config["stage1_patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(ckpt_path),
            monitor="val_accuracy",
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
        verbose=2,
    )

    h = {k: [float(x) for x in v] for k, v in history.history.items()}
    best_val = max(h.get("val_accuracy", [0.0]))
    best_epoch = int(h.get("val_accuracy", [0.0]).index(best_val) + 1) \
        if h.get("val_accuracy") else 0
    report = {
        "best_val_accuracy": float(best_val),
        "best_epoch": best_epoch,
        "total_epochs_run": len(h.get("loss", [])),
        "stage1_lr": float(config["stage1_lr"]),
        "history": h,
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Stage 1 report saved",
                best_val_accuracy=f"{best_val*100:.2f}%",
                path=str(results_path))
    print(f"  >> Saved to : {ckpt_path}")


if __name__ == "__main__":
    main()
