"""TomatoCare — Dataset Loading Utilities
Provides custom tf.data pipelines for loading training, validation, and test images,
ensuring consistent shape formatting and normalization [0, 1] for model input.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import tensorflow as tf


AUTOTUNE = tf.data.AUTOTUNE


def _decode_and_normalise(path: tf.Tensor, label: tf.Tensor,
                          img_size: int) -> tuple[tf.Tensor, tf.Tensor]:
    # 1. Read the image binary contents from path
    raw = tf.io.read_file(path)
    # 2. Decode the raw image bytes to RGB tensor
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    # 3. Resize image to canonical dimensions (e.g. 224x224)
    img = tf.image.resize(img, [img_size, img_size])
    # 4. Normalize pixel values from [0, 255] integers to [0.0, 1.0] floats
    img = tf.cast(img, tf.float32) / 255.0
    img.set_shape([img_size, img_size, 3])
    return img, label


# Converts integer class labels to one-hot encoded vectors (e.g. index 3 -> [0, 0, 0, 1, ...])
def _one_hot(label_idx: tf.Tensor, num_classes: int) -> tf.Tensor:
    return tf.one_hot(label_idx, depth=num_classes, dtype=tf.float32)


def build_split_dataset(split_csv: Path, config: dict,
                        shuffle: bool = False) -> tf.data.Dataset:
    """Build a tf.data.Dataset from a CSV (val or test)."""
    # Reads image paths and labels from the CSV split file, then decodes and normalizes them for the model
    df = pd.read_csv(split_csv)
    paths = df["filepath"].tolist()
    labels = df["class_index"].astype(int).tolist()
    num_classes = len(config["classes"])
    img_size = config["img_size"]
    batch = config["batch_size"]

    # 5. Load filepaths and class indexes as tf.data Slices
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=min(len(paths), 4096), seed=42,
                        reshuffle_each_iteration=True)
    # 6. Apply decoding, resizing, and normalization map function
    ds = ds.map(
        lambda p, l: _decode_and_normalise(p, _one_hot(l, num_classes),
                                           img_size),
        num_parallel_calls=AUTOTUNE,
    )
    # 7. Group into batch sizes and set up prefetching
    ds = ds.batch(batch).prefetch(AUTOTUNE)
    return ds


def build_train_dataset(augmented_train_dir: Path,
                        config: dict) -> tf.data.Dataset:
    """Build the training dataset from the offline-augmented directory."""
    img_size = config["img_size"]
    batch = config["batch_size"]
    classes = config["classes"]

    # 8. Load directory images in batch format, enforcing classes alphabetical index parity
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

    # 9. Normalize training images from [0, 255] uint8 to [0, 1] float32
    ds = ds.map(
        lambda x, y: (tf.cast(x, tf.float32) / 255.0, y),
        num_parallel_calls=AUTOTUNE,
    )
    return ds.prefetch(AUTOTUNE)

