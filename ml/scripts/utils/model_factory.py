"""TomatoCare — Model Factory Utilities
Serves as the single source of truth for model architecture, constructing MobileNetV3 
backbones and classifier layers consistently across scripts.
"""
from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import layers, models
# pyrefly: ignore [missing-import]
from tensorflow.keras.applications import MobileNetV3Large


def build_model(num_classes: int, img_size: int = 224,
                dropout_rate: float = 0.4) -> tf.keras.Model:
    """MobileNetV3-Large backbone + GAP + Dropout + Dense(softmax)."""
    # 1. Instantiate the MobileNetV3 backbone model with ImageNet pre-trained weights
    base = MobileNetV3Large(
        include_top=False,
        weights="imagenet",
        input_shape=(img_size, img_size, 3),
        include_preprocessing=False, # We implement our own rescaling below
        pooling=None,
    )
    base.trainable = False  # Frozen by default for Stage 1

    # 2. Define input shape layer
    inputs = layers.Input(shape=(img_size, img_size, 3), name="image")
    
    # 3. Rescale pixel values from [0, 1] range to MobileNetV3's expected [-1, 1] range
    # This keeps preprocessing consistent between Android assets and Python scripts.
    x = layers.Rescaling(scale=2.0, offset=-1.0, name="to_mobilenet_range")(inputs)
    
    # 4. Pass inputs through MobileNetV3 feature extractor backbone
    x = base(x)
    
    # 5. Global Average Pooling (GAP) collapses 2D feature map dimensions
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    
    # 6. Dropout layer reduces overfitting during head training
    x = layers.Dropout(dropout_rate, name="dropout")(x)
    
    # 7. Dense layer outputs softmax class probabilities (e.g. 11 classes)
    outputs = layers.Dense(num_classes, activation="softmax",
                           name="predictions")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="TomatoCare")
    return model


def unfreeze_top_layers(model: tf.keras.Model,
                        fine_tune_from_layer: int = -30) -> None:
    """Unfreeze the last N layers of the base model for Stage 2."""
    # 8. Locate the MobileNetV3 backbone model among model layers
    base = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            base = layer
            break
    if base is None:
        raise RuntimeError("Could not locate MobileNetV3 backbone in model.")
        
    # 9. Unfreeze only the last N layers (e.g., top 30 layers) for fine-tuning
    base.trainable = True
    for layer in base.layers[:fine_tune_from_layer]:
        layer.trainable = False
        
    # 10. Ensure BatchNormalization layers inside frozen layers stay in inference mode
    # This preserves running variance/mean statistics
    for layer in base.layers[:fine_tune_from_layer]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
