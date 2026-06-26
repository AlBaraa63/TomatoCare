"""TomatoCare — Stage 1: Classifier Head Training
Freezes the MobileNetV3 base model and trains only the custom output layers
to map pre-trained features to our tomato classes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402





def compute_class_weights(augmented_train_dir: Path,
                          classes: list[str],
                          mode: str = "balanced",
                          manual: dict | None = None) -> dict[int, float]:
    """Return {class_index: weight} from the actual augmented training set.

    'balanced' mirrors sklearn's compute_class_weight: n_samples / (n_classes * count_c).
    The augmented folder is the ground truth for what the model will see —
    counting train.csv would miss the 4x augmentation multiplier.
    """
    # If weighting is turned off, assign a neutral weight of 1.0 to all classes
    if mode == "none":
        return {i: 1.0 for i in range(len(classes))}
        
    # If using custom weights from the config, read and apply them directly
    if mode == "manual":
        if not manual:
            raise ValueError("class_weights.mode='manual' but manual_weights missing")
        return {int(k): float(v) for k, v in manual.items()}
        
    # Balanced mode: Adjust weights automatically based on class size
    counts: dict[int, int] = {}
    total = 0
    
    # 1. Count the number of images in each disease folder on the disk
    for idx, cls in enumerate(classes):
        cls_dir = augmented_train_dir / cls
        if cls_dir.exists():
            n = sum(1 for p in cls_dir.iterdir() if p.is_file())
        else:
            n = 0
        counts[idx] = n
        total += n
        
    # 2. Calculate the weight: Rare classes get higher weights, common classes get lower weights.
    # Formula: total_images / (number_of_classes * images_in_this_class)
    n_classes = len(classes)
    weights: dict[int, float] = {}
    for idx in range(n_classes):
        c = max(counts[idx], 1)
        weights[idx] = total / (n_classes * c)
    return weights


def main() -> None:
    # STEP 1: Set the random seed to 42 for absolute reproducibility
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset, build_train_dataset
    from utils.model_factory import build_model

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    print(f"--- TomatoCare — Stage 1 Training (head only) ({device}) ---")

    # STEP 2: Set up paths for model checkpoints and metric results
    config = load_config()
    root = project_root()
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    results_dir = root / config["paths"]["results_dir"]
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    ckpt_path = ckpt_dir / "stage1_best.keras"
    results_path = results_dir / "results_stage1.json"

    # STEP 3: Check if we already have a trained checkpoint (avoids duplicate runs)
    if ckpt_path.exists() and results_path.exists():
        print(f"SKIP: {ckpt_path} already exists. Delete to re-run.")
        with open(results_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    print("--- Building Datasets ---")
    # STEP 4: Load training dataset (with augmentations) and validation dataset
    augmented_train_dir = root / config["paths"]["augmented_dir"] / "train"
    train_ds = build_train_dataset(augmented_train_dir, config)
    val_ds = build_split_dataset(
        root / config["paths"]["splits_dir"] / "val.csv", config)
    print(f"Datasets built: batch_size={config['batch_size']}, img_size={config['img_size']}")

    print("--- Computing Class Weights ---")
    # STEP 5: Compute class weights so the larger "Not A Leaf" class does not bias the model
    cw_cfg = config.get("class_weights") or {}
    class_weight = compute_class_weights(
        augmented_train_dir, config["classes"],
        mode=cw_cfg.get("mode", "balanced"),
        manual=cw_cfg.get("manual_weights"),
    )
    for idx, cls in enumerate(config["classes"]):
        print(f"Class weight: {cls} = {class_weight[idx]:.3f}")

    # STEP 6: Build our model: Pretrained MobileNetV3 + custom Classification Head
    # EXPLANATION FOR PRESENTATION: We load Google's MobileNetV3 (which already knows general vision shapes) 
    # and freeze its weights. We add our own new layer (the head) on top. This is called Transfer Learning.
    model = build_model(num_classes=len(config["classes"]),
                        img_size=config["img_size"],
                        dropout_rate=config["dropout_rate"])
    label_smoothing = float((config.get("loss") or {}).get("label_smoothing", 0.0))
    # Compile with Adam optimizer and Categorical Crossentropy loss + Label Smoothing
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
    print(f"Model built: MobileNetV3-Large (base frozen). Trainable: {trainable:,} | Total: {total:,}")

    # STEP 7: Set up early stopping and best model checkpoints
    callbacks = [
        # Stop training if the validation loss stops improving (prevents overfitting)
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            mode="min",
            patience=config["stage1_patience"],
            restore_best_weights=True,
            verbose=1,
        ),
        # Save the best model state based on lowest validation loss
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(ckpt_path),
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1,
        ),
    ]

    # STEP 8: Fit/Train the classification head
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["stage1_epochs"],
        callbacks=callbacks,
        class_weight=class_weight,
        verbose=2,
    )

    # STEP 9: Compute best metrics and write results to JSON report
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
    print(f"Stage 1 report saved to: {results_path} | Best Val Acc: {best_val_acc*100:.2f}%")
    print(f"Model saved to: {ckpt_path}")


if __name__ == "__main__":
    main()
