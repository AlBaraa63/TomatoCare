"""TomatoCare — Custom Neural Network Layers
Defines the TemperatureScale calibration layer used to post-process model logits before softmax.
"""
from __future__ import annotations

import tensorflow as tf


class TemperatureScale(tf.keras.layers.Layer):
    """Divides logits by a fixed scalar temperature before softmax.

    This bakes the post-hoc calibration directly into the model structure,
    meaning the exported TFLite graph performs calibration on-device automatically.
    """

    def __init__(self, temperature: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.temperature = float(temperature)

    def call(self, inputs):
        return inputs / self.temperature

    def get_config(self):
        cfg = super().get_config()
        cfg["temperature"] = self.temperature
        return cfg
