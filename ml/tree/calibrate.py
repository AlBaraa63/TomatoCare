"""TREE / calibrate — temperature-scale the disease classifier's confidence.

Why: the app shows a LOW-CONFIDENCE banner when top probability < 0.60. That
threshold only means something if the softmax probabilities are calibrated
(i.e. "0.9" really happens ~90% of the time). Modern CNNs are usually
over-confident, so we apply temperature scaling (Guo et al. 2017): fit a single
scalar T on the validation set that softens the logits.

Trick for clean export: logits/T = (feat @ W + b)/T = feat @ (W/T) + (b/T).
So we just divide the FINAL DENSE layer's weights and bias by T. No extra
Lambda/division op in the graph -> TFLite stays simple, and argmax (accuracy)
is unchanged — only the confidence distribution is corrected.

Run inside the WSL venv (after training stage3):
    python ml/tree/calibrate.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import tensorflow as tf
from scipy.optimize import minimize_scalar

IMG = 224
AUTOTUNE = tf.data.AUTOTUNE
MODELS = Path.home() / "tc_data" / "models"
VAL_DIR = Path.home() / "tc_data" / "stage3_disease" / "val"
CKPT = MODELS / "stage3_disease.keras"


def ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    conf = probs.max(1)
    correct = probs.argmax(1) == labels
    edges = np.linspace(0, 1, n_bins + 1)
    e = 0.0
    for i in range(n_bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.any():
            e += abs(correct[m].mean() - conf[m].mean()) * m.mean()
    return float(e)


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def main() -> None:
    model = tf.keras.models.load_model(CKPT)

    # Features feeding the final Dense (Dropout is a no-op at inference).
    feat_model = tf.keras.Model(model.inputs, model.layers[-1].input)
    dense = model.layers[-1]
    W, b = dense.get_weights()

    ds = tf.keras.utils.image_dataset_from_directory(
        VAL_DIR, labels="inferred", label_mode="int",
        image_size=(IMG, IMG), crop_to_aspect_ratio=True,
        batch_size=64, shuffle=False)
    ds = ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y),
                num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
    labels = np.concatenate([y.numpy() for _, y in ds])
    feats = feat_model.predict(ds, verbose=0)
    logits = feats @ W + b

    def nll(T: float) -> float:
        logp = np.log(softmax(logits / T) + 1e-12)
        return -logp[np.arange(len(labels)), labels].mean()

    res = minimize_scalar(nll, bounds=(0.05, 10.0), method="bounded")
    T = float(res.x)

    ece_before = ece(softmax(logits), labels)
    ece_after = ece(softmax(logits / T), labels)
    acc = float((softmax(logits).argmax(1) == labels).mean())

    print(f"Temperature T   : {T:.4f}")
    print(f"Val accuracy    : {acc:.4f}  (unchanged by scaling)")
    print(f"ECE before      : {ece_before:.4f}")
    print(f"ECE after       : {ece_after:.4f}")

    # Bake T into the final Dense and overwrite the checkpoint (keep a backup).
    shutil.copy2(CKPT, MODELS / "stage3_disease.uncalibrated.keras")
    dense.set_weights([W / T, b / T])
    model.save(CKPT)

    meta_path = MODELS / "stage3_disease.meta.json"
    meta = json.loads(meta_path.read_text())
    meta["temperature"] = T
    meta["ece_before"] = round(ece_before, 4)
    meta["ece_after"] = round(ece_after, 4)
    meta["calibrated"] = True
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"[done] calibrated model saved (backup: stage3_disease.uncalibrated.keras)")


if __name__ == "__main__":
    main()
