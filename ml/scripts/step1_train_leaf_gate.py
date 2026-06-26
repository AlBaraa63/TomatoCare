"""TomatoCare — Step 1: Train Leaf Gate
Trains the binary Leaf Gate model (leaf vs. not_leaf) to reject non-leaf images.
Uses two-phase transfer learning (head training first, then unfreezing top layers).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed

# Pinned Image Size and Random Seed
IMG_SIZE = 224
SEED = 42


def make_dataset(directory: Path, batch_size: int, is_training: bool) -> tuple:
    """Loads directory, rescales pixels to [0, 1], and configures batching."""
    import tensorflow as tf
    ds = tf.keras.utils.image_dataset_from_directory(
        directory,
        labels="inferred",
        label_mode="categorical",
        image_size=(IMG_SIZE, IMG_SIZE),
        crop_to_aspect_ratio=True,
        batch_size=batch_size,
        shuffle=is_training,
        seed=SEED,
    )
    class_names = ds.class_names
    
    # Scale pixel values [0, 255] -> [0.0, 1.0] (matching Android Preprocessor)
    ds = ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y),
                 num_parallel_calls=tf.data.AUTOTUNE)
                 
    # Apply basic horizontal flip augmentation during training
    if is_training:
        ds = (ds.unbatch()
                .map(lambda x, y: (tf.image.random_flip_left_right(x), y),
                     num_parallel_calls=tf.data.AUTOTUNE)
                .batch(batch_size))
                
    return ds.prefetch(tf.data.AUTOTUNE), class_names


def calculate_class_weights(directory: Path, class_names: list[str]) -> dict[int, float]:
    """Computes balanced class weights to handle imbalanced datasets."""
    counts = []
    for c in class_names:
        counts.append(sum(1 for _ in (directory / c).iterdir()))
    counts = np.array(counts, dtype=np.float64)
    total = counts.sum()
    weights = total / (len(class_names) * counts)
    return {i: float(weights[i]) for i in range(len(class_names))}


def build_leaf_model(num_classes: int) -> tuple:
    """Builds MobileNetV3-Small backbone + GAP + Dropout + Classifier Head."""
    import tensorflow as tf
    base = tf.keras.applications.MobileNetV3Small(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
        include_preprocessing=False, # Pixel normalization [0,1] handled in dataset loader
    )
    base.trainable = False  # Backbone frozen for Stage 1 head-training
    
    inp = tf.keras.Input((IMG_SIZE, IMG_SIZE, 3))
    x = base(inp, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    out = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inp, out), base


def main() -> None:
    set_seed(SEED)
    import tensorflow as tf

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    print(f"--- TomatoCare — Step 1: Training Leaf Gate ({device}) ---")

    config = load_config()
    root = project_root()
    
    data_dir = Path(config["paths"].get("data_dir", str(Path.home() / "tc_data"))) / "stage1_leaf"
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    
    ckpt_path = ckpt_dir / "stage1_leaf.keras"
    results_path = root / config["paths"]["results_dir"] / "results_leaf_gate.json"

    # Avoid duplicate runs if model already trained
    if ckpt_path.exists() and results_path.exists():
        print(f"SKIP: {ckpt_path} already exists. Delete to re-run.")
        return

    print("--- Loading Datasets ---")
    train_ds, class_names = make_dataset(data_dir / "train", config["batch_size"], True)
    val_ds, _ = make_dataset(data_dir / "val", config["batch_size"], False)
    print(f"Loaded classes: {class_names}")

    print("--- Computing Class Weights ---")
    class_weights = calculate_class_weights(data_dir / "train", class_names)
    print(f"Computed weights: {class_weights}")

    print("--- Building Model ---")
    model, base_backbone = build_leaf_model(len(class_names))
    
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            str(ckpt_path), monitor="val_accuracy", save_best_only=True, mode="max", verbose=1),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, mode="max", restore_best_weights=True, verbose=1),
    ]

    print("--- Stage 1: Training Head Only ---")
    # EXPLANATION FOR PRESENTATION: We keep Google's MobileNetV3-Small backbone frozen and train only
    # our custom decision head first, allowing the network to adapt to the new categories.
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
        metrics=["accuracy"],
    )
    h1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=12,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=2,
    )

    print("--- Stage 2: Fine-Tuning Backbone ---")
    # EXPLANATION FOR PRESENTATION: We unfreeze the last 30 layers of MobileNetV3-Small and train at a
    # 10x slower learning rate (0.0001) to adapt the backbone feature extraction layers to leaf shapes.
    base_backbone.trainable = True
    for layer in base_backbone.layers[:-30]:
        layer.trainable = False
        
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-4),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
        metrics=["accuracy"],
    )
    h2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=6,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=2,
    )

    # Save training report metrics
    best_val_acc = max(h1.history["val_accuracy"] + h2.history["val_accuracy"])
    report = {
        "stage": "stage1_leaf",
        "best_val_accuracy": float(best_val_acc),
        "classes": class_names,
    }
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"Leaf Gate report saved to: {results_path} | Best Val Acc: {best_val_acc*100:.2f}%")
    print(f"Model saved to: {ckpt_path}")


if __name__ == "__main__":
    main()
