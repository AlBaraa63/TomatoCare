from __future__ import annotations


def get_temperature_scale_layer():
    """Return TemperatureScale class (imported lazily to avoid top-level TF import)."""
    import tensorflow as tf

    class TemperatureScale(tf.keras.layers.Layer):
        """Divides logits by a fixed scalar temperature before softmax.

        Serialises cleanly (no Lambda closure), so load_model works without
        safe_mode tricks and TFLite conversion produces a single DIV op.
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

    return TemperatureScale
