"""Reproducibility seeding for every training script.

Called at the very start of every script that touches randomness:
weight initialisation, data shuffles, dropout masks, augmentation
randomisation. Pinning the seed lets us re-run a training and get
within 0.1% of the same val accuracy, which is what makes the 90%
target verifiable rather than just lucky.
"""
from __future__ import annotations

import os
import random


def set_seed(seed: int = 42) -> None:
    # Order matters: PYTHONHASHSEED has to be set before any module that
    # uses dict ordering for ML purposes is touched. We also re-export it
    # in case a sub-process spawned by tf.data inherits the env.
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    # NumPy and TensorFlow imports are local so that a script can call
    # set_seed() before doing anything else (incl. importing TF) and still
    # get the env var set ahead of TF's internal hashing.
    import numpy as np
    np.random.seed(seed)

    import tensorflow as tf
    tf.random.set_seed(seed)
    tf.keras.utils.set_random_seed(seed)
    # Deterministic ops trade ~10% throughput for bit-identical runs on
    # the same GPU. Worth it for a capstone graded on reproducibility.
    tf.config.experimental.enable_op_determinism()


def load_config(path: str = "ml/configs/training_config.yaml") -> dict:
    """Single entry point for every script to read training_config.yaml.

    Resolves the path relative to the project root so scripts work
    whether you launch from project root or ml/ directory.
    """
    from pathlib import Path
    import yaml

    config_path = Path(path)
    if not config_path.exists():
        # Try resolving from project root (parent of ml/)
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
