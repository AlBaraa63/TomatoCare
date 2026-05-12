"""A4 — tf.data builders shared by Stage 1, Stage 2, and eval.

Two callers:
  - Train: build_train_dataset() reads the *augmented* train directory
    (one image per file, already pre-augmented by A3) — no on-the-fly aug.
  - Val/Test: build_split_dataset() reads from val.csv / test.csv —
    resize + normalise only, no augmentation.

Output spec (mandatory, matches model input):
  - image: float32, shape (224, 224, 3), values in [0.0, 1.0]
  - label: float32, shape (10,), one-hot
  - batched to config['batch_size'], prefetched with AUTOTUNE.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import tensorflow as tf


AUTOTUNE = tf.data.AUTOTUNE


def _decode_and_normalise(path: tf.Tensor, label: tf.Tensor,
                          img_size: int) -> tuple[tf.Tensor, tf.Tensor]:
    raw = tf.io.read_file(path)
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    img = tf.image.resize(img, [img_size, img_size])
    img = tf.cast(img, tf.float32) / 255.0
    img.set_shape([img_size, img_size, 3])
    return img, label


def _one_hot(label_idx: tf.Tensor, num_classes: int) -> tf.Tensor:
    return tf.one_hot(label_idx, depth=num_classes, dtype=tf.float32)


def build_split_dataset(split_csv: Path, config: dict,
                        shuffle: bool = False) -> tf.data.Dataset:
    """Build a tf.data.Dataset from a CSV (val or test).

    The CSV must have columns: filepath, label, class_index.
    """
    df = pd.read_csv(split_csv)
    paths = df["filepath"].tolist()
    labels = df["class_index"].astype(int).tolist()
    num_classes = len(config["classes"])
    img_size = config["img_size"]
    batch = config["batch_size"]

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=min(len(paths), 4096), seed=42,
                        reshuffle_each_iteration=True)
    ds = ds.map(
        lambda p, l: _decode_and_normalise(p, _one_hot(l, num_classes),
                                           img_size),
        num_parallel_calls=AUTOTUNE,
    )
    ds = ds.batch(batch).prefetch(AUTOTUNE)
    return ds


def build_train_dataset(augmented_train_dir: Path,
                        config: dict) -> tf.data.Dataset:
    """Build the training dataset from the offline-augmented directory.

    Uses image_dataset_from_directory because A3 already laid the data out
    in <class>/<image>.jpg form — letting Keras infer labels keeps the
    class_indices ordering consistent with eval/inference.
    """
    img_size = config["img_size"]
    batch = config["batch_size"]
    classes = config["classes"]

    ds = tf.keras.utils.image_dataset_from_directory(
        directory=str(augmented_train_dir),
        labels="inferred",
        label_mode="categorical",
        class_names=classes,         # pin the order to our canonical list
        color_mode="rgb",
        batch_size=batch,
        image_size=(img_size, img_size),
        shuffle=True,
        seed=42,
        interpolation="bilinear",
    )

    # image_dataset_from_directory returns uint8 [0,255]; normalise to [0,1].
    ds = ds.map(
        lambda x, y: (tf.cast(x, tf.float32) / 255.0, y),
        num_parallel_calls=AUTOTUNE,
    )
    return ds.prefetch(AUTOTUNE)


def build_dataset(split_csv: Path, config: dict,
                  augment: bool = False) -> tf.data.Dataset:
    """Spec-compliant entry point per the prompt.

    augment=True is a legacy hook — A3 produces augmented data offline, so
    callers should prefer build_train_dataset() for training. We keep this
    here to satisfy the prompt's exact function signature.
    """
    if augment:
        raise NotImplementedError(
            "On-the-fly augmentation is disabled — A3 writes augmented "
            "images to disk for reproducibility. Use build_train_dataset() "
            "with paths['augmented_dir'] for training."
        )
    return build_split_dataset(split_csv, config, shuffle=False)
