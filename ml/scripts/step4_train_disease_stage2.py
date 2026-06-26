"""TomatoCare — Stage 2: Model Fine-Tuning
Loads Stage 1 weights, unfreezes the top 30 layers of MobileNetV3,
and trains with a low learning rate (1e-4) to learn specific visual features.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402
from step1_train_stage1 import compute_class_weights  # noqa: E402





def main() -> None:
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset, build_train_dataset
    from utils.model_factory import build_model, unfreeze_top_layers

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    print(f"--- TomatoCare — Stage 2 Fine-Tuning ({device}) ---")

    config = load_config()
    root = project_root()
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    results_dir = root / config["paths"]["results_dir"]

    stage1_ckpt = ckpt_dir / "stage1_best.keras"
    stage2_ckpt = ckpt_dir / "stage2_best.keras"
    results_path = results_dir / "results_stage2.json"

    # STEP 1: Verify that Stage 1 check-point exists before proceeding
    if not stage1_ckpt.exists():
        raise FileNotFoundError(
            f"{stage1_ckpt} not found. Run train_stage1.py first."
        )

    # STEP 2: Check if Stage 2 is already complete to avoid duplicate work
    if stage2_ckpt.exists() and results_path.exists():
        print(f"  >> SKIP: {stage2_ckpt} already exists. Delete to re-run.")
        with open(results_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    print("--- Loading Stage 1 Checkpoint ---")
    # STEP 3: Load the pre-trained weights from Stage 1. 
    # We rebuild the model and set weights by value so we don't carry frozen states.
    _loaded = tf.keras.models.load_model(str(stage1_ckpt))
    model = build_model(
        num_classes=len(config["classes"]),
        img_size=config["img_size"],
        dropout_rate=config["dropout_rate"],
    )
    model.set_weights(_loaded.get_weights())
    del _loaded
    print(f"Stage 1 best weights loaded from: {stage1_ckpt}")

    print("--- Building Datasets ---")
    # STEP 4: Build datasets
    augmented_train_dir = root / config["paths"]["augmented_dir"] / "train"
    train_ds = build_train_dataset(augmented_train_dir, config)
    val_ds = build_split_dataset(
        root / config["paths"]["splits_dir"] / "val.csv", config)

    print("--- Computing Class Weights ---")
    # STEP 5: Compute class weights
    cw_cfg = config.get("class_weights") or {}
    class_weight = compute_class_weights(
        augmented_train_dir, config["classes"],
        mode=cw_cfg.get("mode", "balanced"),
        manual=cw_cfg.get("manual_weights"),
    )
    for idx, cls in enumerate(config["classes"]):
        print(f"Class weight: {cls} = {class_weight[idx]:.3f}")

    print("--- Unfreezing Top Layers ---")
    # STEP 6: Unfreeze the last N layers of the MobileNetV3 base model (e.g. last 30 layers)
    # EXPLANATION FOR PRESENTATION: We unfreeze the top 30 layers of the main neural network brain.
    # This is called Fine-Tuning. It allows the model's visual sensors to slightly adjust to recognize 
    # the specific, detailed textures of tomato diseases (like spots, mold, and discoloration).
    unfreeze_top_layers(model, config["fine_tune_from_layer"])
    
    # STEP 7: Re-compile the model with a much lower Stage 2 learning rate (e.g. 0.0001)
    # EXPLANATION FOR PRESENTATION: We use a 10x slower learning rate so we don't destroy the original 
    # visual features (ImageNet knowledge) that the model already knows.
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
    print(f"Unfrozen last {abs(config['fine_tune_from_layer'])} layers. Trainable: {trainable:,}")

    print("--- Stage 2 Training — Fine-Tune ---")
    # STEP 8: Set up callbacks (Early Stopping & Checkpoints)
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



    # STEP 9: Fit/Train the top un-frozen layers of the base model
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["stage2_epochs"],
        callbacks=callbacks,
        class_weight=class_weight,
        verbose=2,
    )

    # STEP 10: Compute best metrics and write results to JSON report
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
    print(f"Stage 2 report saved to: {results_path} | Best Val Acc: {best_val_acc*100:.2f}%")
    print(f"Model saved to: {stage2_ckpt}")


if __name__ == "__main__":
    main()
