"""TREE / train — one trainer for all three stages of the decision tree.

    stage1_leaf    : binary  leaf vs not_leaf      (MobileNetV3-Small)
    stage2_tomato  : binary  tomato vs other_leaf  (MobileNetV3-Small)
    stage3_disease : 11-class tomato diagnosis      (MobileNetV3-Large)

Two-phase transfer learning (same recipe v1 used and that the report describes):
  Phase 1 — freeze the ImageNet backbone, train only the new head.
  Phase 2 — unfreeze the top block, fine-tune at a low LR.

CONTRACT-CRITICAL — preprocessing parity with the Android app:
  The Kotlin ImagePreprocessor feeds pixels as float32 in [0,1] (divide by
  255, NO ImageNet mean/std). So we:
    * scale images to [0,1] in the tf.data pipeline, and
    * build MobileNetV3 with include_preprocessing=False (no rescaling baked
      into the graph).
  The exported TFLite model therefore expects [0,1] exactly like the app
  sends. Do not "fix" this by adding a Rescaling layer — it would double-scale.

Run inside the WSL venv, e.g.:
    python ml/tree/train.py --stage stage3_disease
    python ml/tree/train.py --stage stage1_leaf --epochs-head 12 --epochs-ft 6
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

AUTOTUNE = tf.data.AUTOTUNE
IMG = 224
SEED = 42

# Per-stage defaults. Gates are binary + small backbone; disease is the big one.
STAGES = {
    "stage1_leaf":    {"backbone": "small", "epochs_head": 12, "epochs_ft": 6},
    "stage2_tomato":  {"backbone": "small", "epochs_head": 12, "epochs_ft": 6},
    "stage3_disease": {"backbone": "large", "epochs_head": 20, "epochs_ft": 10},
}


def make_ds(directory: Path, batch: int, training: bool):
    """image_dataset_from_directory -> [0,1] -> (train: augment) -> prefetch."""
    ds = tf.keras.utils.image_dataset_from_directory(
        directory,
        labels="inferred",
        label_mode="categorical",
        image_size=(IMG, IMG),
        crop_to_aspect_ratio=True,   # center-crop, never squash (no distortion)
        batch_size=batch,
        shuffle=training,
        seed=SEED,
    )
    class_names = ds.class_names

    # [0,255] uint8 -> [0,1] float32 (matches Android ImagePreprocessor).
    ds = ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y),
                num_parallel_calls=AUTOTUNE)

    if training:
        # Light on-the-fly augmentation (kept in the data pipeline, NOT the
        # model, so the exported graph stays clean).
        def augment(x, y):
            x = tf.image.random_flip_left_right(x, seed=SEED)
            x = tf.image.random_brightness(x, 0.15, seed=SEED)
            x = tf.image.random_contrast(x, 0.85, 1.15, seed=SEED)
            x = tf.clip_by_value(x, 0.0, 1.0)
            return x, y
        ds = ds.map(augment, num_parallel_calls=AUTOTUNE)

    return ds.prefetch(AUTOTUNE), class_names


def class_weights_from_dir(directory: Path, class_names: list[str]) -> dict[int, float]:
    """balanced weights = n_total / (n_classes * count_c)."""
    counts = []
    for c in class_names:
        counts.append(sum(1 for _ in (directory / c).iterdir()))
    counts = np.array(counts, dtype=np.float64)
    total = counts.sum()
    w = total / (len(class_names) * counts)
    return {i: float(w[i]) for i in range(len(class_names))}


def build_model(num_classes: int, backbone: str):
    base_cls = (tf.keras.applications.MobileNetV3Large if backbone == "large"
                else tf.keras.applications.MobileNetV3Small)
    base = base_cls(
        input_shape=(IMG, IMG, 3),
        include_top=False,
        weights="imagenet",
        include_preprocessing=False,   # we feed [0,1] ourselves — parity!
    )
    base.trainable = False
    inp = tf.keras.Input((IMG, IMG, 3))
    x = base(inp, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    out = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inp, out), base


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGES))
    ap.add_argument("--data", default=str(Path.home() / "tc_data"))
    ap.add_argument("--out", default=str(Path.home() / "tc_data" / "models"))
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--epochs-head", type=int, default=None)
    ap.add_argument("--epochs-ft", type=int, default=None)
    args = ap.parse_args()

    cfg = STAGES[args.stage]
    epochs_head = args.epochs_head or cfg["epochs_head"]
    epochs_ft = args.epochs_ft or cfg["epochs_ft"]

    tf.keras.utils.set_random_seed(SEED)
    stage_dir = Path(args.data) / args.stage
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"==== TRAIN {args.stage} (backbone={cfg['backbone']}) ====")
    train_ds, class_names = make_ds(stage_dir / "train", args.batch, True)
    val_ds, _ = make_ds(stage_dir / "val", args.batch, False)
    num_classes = len(class_names)
    print(f"classes ({num_classes}): {class_names}")

    cw = class_weights_from_dir(stage_dir / "train", class_names)
    print(f"class weights: {cw}")

    model, base = build_model(num_classes, cfg["backbone"])
    ckpt = out_dir / f"{args.stage}.keras"
    cbs = [
        tf.keras.callbacks.ModelCheckpoint(
            str(ckpt), monitor="val_accuracy", save_best_only=True, mode="max"),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, mode="max",
            restore_best_weights=True),
    ]

    # ---- Phase 1: head only ----
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
                  metrics=["accuracy"])
    h1 = model.fit(train_ds, validation_data=val_ds, epochs=epochs_head,
                   class_weight=cw, callbacks=cbs)

    # ---- Phase 2: fine-tune top of backbone ----
    base.trainable = True
    for layer in base.layers[:-30]:      # unfreeze last 30 layers only
        layer.trainable = False
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-4),
                  loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
                  metrics=["accuracy"])
    h2 = model.fit(train_ds, validation_data=val_ds, epochs=epochs_ft,
                   class_weight=cw, callbacks=cbs)

    best_val = max(h1.history["val_accuracy"] + h2.history["val_accuracy"])
    meta = {
        "stage": args.stage,
        "backbone": cfg["backbone"],
        "class_names": class_names,
        "num_classes": num_classes,
        "best_val_accuracy": float(best_val),
        "input_range": "[0,1]",
        "img_size": IMG,
    }
    (out_dir / f"{args.stage}.meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[done] best val_acc={best_val:.4f}  saved -> {ckpt}")


if __name__ == "__main__":
    main()
