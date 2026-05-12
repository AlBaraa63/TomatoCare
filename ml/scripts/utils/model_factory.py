"""Shared model factory — single source of truth for architecture.

Per the protocol: "Model architecture never defined inside training scripts."
Both train_stage1, train_stage2, eval_model, and export_tflite call into
this module so any architecture change happens in exactly one place.
"""
from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV3Large


def build_model(num_classes: int, img_size: int = 224,
                dropout_rate: float = 0.4) -> tf.keras.Model:
    """MobileNetV3-Large backbone + GAP + Dropout + Dense(softmax).

    Base model uses ImageNet pretrained weights. Trainability is set by
    the caller (Stage 1 freezes; Stage 2 unfreezes the top N layers).
    """
    base = MobileNetV3Large(
        include_top=False,
        weights="imagenet",
        input_shape=(img_size, img_size, 3),
        # include_preprocessing=False because we provide our own rescale
        # below. The model's built-in preprocessing would expect [0,255]
        # and would double-scale our pre-normalised inputs.
        include_preprocessing=False,
        pooling=None,
    )
    base.trainable = False  # Stage 1 default; Stage 2 reassigns this.

    inputs = layers.Input(shape=(img_size, img_size, 3), name="image")
    # Our dataset_loader and Android ImagePreprocessor both produce [0,1]
    # float32. MobileNetV3-Large's ImageNet weights expect [-1,1]. Baking
    # the rescale into the graph keeps both pipelines in sync and means
    # the TFLite export carries the correct preprocessing automatically.
    x = layers.Rescaling(scale=2.0, offset=-1.0, name="to_mobilenet_range")(inputs)
    # Do not pass training=False here. Keras propagates the model-level
    # training flag through each layer's trainable attribute:
    #   Stage 1 — base.trainable=False → all BN runs in inference mode.
    #   Stage 2 — top layers trainable=True → their BN runs in training
    #   mode so gradients flow correctly; frozen-bottom BN stays inference.
    # Hardcoding training=False breaks Stage 2 backprop through BN on GPU
    # (FusedBatchNormGradV3 requires training=True for gradient computation).
    x = base(x)
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax",
                           name="predictions")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="TomatoCare")
    return model


def unfreeze_top_layers(model: tf.keras.Model,
                        fine_tune_from_layer: int = -30) -> None:
    """Unfreeze the last N layers of the base model for Stage 2.

    fine_tune_from_layer is a Python slice index. -30 means "the last 30
    layers". MobileNetV3-Large has ~280 layers; unfreezing only the top
    ~30 keeps the low-level edge/colour features that ImageNet learned
    intact while letting the high-level lesion-shape features adapt.
    """
    # The base model is the first non-Input layer wrapped inside our Model.
    base = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            base = layer
            break
    if base is None:
        raise RuntimeError("Could not locate MobileNetV3 backbone in model.")
    base.trainable = True
    for layer in base.layers[:fine_tune_from_layer]:
        layer.trainable = False
    # BatchNorm in frozen layers must stay in inference mode to avoid
    # destroying running statistics during fine-tune.
    for layer in base.layers[:fine_tune_from_layer]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
