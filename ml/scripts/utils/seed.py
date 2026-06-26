"""TomatoCare — Reproducibility Seeding Utilities
Sets environmental variables and random seeds for Python, NumPy, and TensorFlow,
ensuring bit-identical and reproducible training/evaluation executions.
"""
from PIL import ImagePath
from __future__ import annotations

import os
import random


def set_seed(seed: int = 42) -> None:
    # 1. Set environment variable for Python hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)
    # 2. Seed basic Python random module
    random.seed(seed)

    # 3. Seed NumPy random number generator
    import numpy as np
    np.random.seed(seed)

    # 4. Seed TensorFlow and Keras backend generators
    import tensorflow as tf
    tf.random.set_seed(seed)
    tf.keras.utils.set_random_seed(seed)
    # 5. Force TensorFlow to use deterministic math operations (guarantees identical runs)
    tf.config.experimental.enable_op_determinism()


def load_config(path: str = "ml/configs/training_config.yaml") -> dict:
    """Single entry point for every script to read training_config.yaml.

    Resolves the path relative to the project root so scripts work
    whether you launch from project root or ml/ directory.
    """
    from pathlib import Path
    import yaml

    # 6. Resolve config file path (handles executing from different folders)
    config_path = Path(path)
    if not config_path.exists():
        alt = Path(__file__).resolve().parents[3] / path
        if alt.exists():
            config_path = alt
        else:
            raise FileNotFoundError(
                f"training_config.yaml not found at {path} or {alt}. "
                "Run scripts from the project root."
            )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def project_root() -> "Path":
    """Locate the ml/ directory regardless of where the script was launched."""
    from pathlib import Path
    # utils/seed.py → utils/ → scripts/ → ml/
    return Path(__file__).resolve().parents[2]
