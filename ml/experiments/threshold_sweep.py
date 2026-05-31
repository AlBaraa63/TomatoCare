#!/usr/bin/env python3
"""
Experiment: confidence-threshold sweep (selective prediction) for the deployed
Stage-3 disease classifier.

WHAT IT MEASURES
----------------
For each candidate low-confidence threshold tau, this computes:
  * coverage          — fraction of test images whose top softmax >= tau
                        (i.e. the app would SHOW a diagnosis rather than a
                        low-confidence warning)
  * selective accuracy — accuracy on just those covered images
  * rejected           — fraction sent to the low-confidence warning instead

This is the standard risk-coverage / selective-prediction analysis. It directly
evidences the choice of the 0.60 threshold (DR-06 in the report) by showing the
accuracy<->coverage trade-off, rather than asserting it.

WHY IT IS HONEST
----------------
Nothing here is hard-coded or assumed about the result. You run it against the
SHIPPED Stage-3 TFLite model and your held-out test set; it prints and saves the
real numbers. It does NOT retrain, recompute, or alter the deployed model.

REQUIREMENTS
------------
  pip install tensorflow numpy matplotlib pillow
Run from the repo root (or anywhere — paths below are configurable):
  python ml/experiments/threshold_sweep.py

OUTPUTS (written next to this script, under results/)
  threshold_sweep.json   — full table of (tau, coverage, selective_accuracy)
  threshold_sweep.png     — accuracy & coverage vs threshold plot

ASSUMPTIONS YOU MAY NEED TO ADJUST (see CONFIG below)
  * MODEL_PATH points at the deployed Stage-3 float16 TFLite.
  * TEST_DIR contains one subfolder per class, each full of that class's images.
  * LABELS is the model's output-index -> class-name order (read from the app's
    labels.json). Folder names are normalised and matched to these; add to
    FOLDER_ALIASES if your test folders use different names.
  * Preprocessing mirrors the deployed contract: center-crop to the largest
    centred square, resize to 224, scale to [0,1]. Adjust if your pipeline
    differs (it must match the app for the numbers to be valid).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

try:
    import tensorflow as tf
except ImportError as e:  # pragma: no cover - guidance only
    raise SystemExit("TensorFlow is required: pip install tensorflow") from e

# --------------------------------------------------------------------------- #
# CONFIG — edit these to match your machine.
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = REPO_ROOT / "ml" / "models" / "tflite" / "stage3_disease_float16.tflite"
# A directory with one subfolder per class (your held-out test split).
TEST_DIR = REPO_ROOT / "ml" / "dataset" / "test"
# Output-index -> class-name order for the deployed model.
LABELS_PATH = REPO_ROOT / "android" / "app" / "src" / "main" / "assets" / "labels.json"

IMG_SIZE = 224
THRESHOLDS = [round(t, 2) for t in np.arange(0.50, 0.96, 0.05)]

OUT_DIR = Path(__file__).resolve().parent / "results"

# Map test-folder names -> canonical label names, for any that don't normalise
# cleanly. Keys/values are matched after _normalise().
FOLDER_ALIASES: dict[str, str] = {
    # "tomato_spider_mites_two_spotted_spider_mite": "spider_mites",
}


# --------------------------------------------------------------------------- #
def _normalise(name: str) -> str:
    """Lowercase, drop a leading 'tomato_', collapse separators."""
    n = name.strip().lower().replace(" ", "_").replace("-", "_")
    if n.startswith("tomato_"):
        n = n[len("tomato_"):]
    return n


def load_labels() -> list[str]:
    """Load the model's class order. Accepts a JSON list or {index: name} dict."""
    raw = json.loads(Path(LABELS_PATH).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        names = [raw[k] for k in sorted(raw, key=lambda x: int(x))]
    else:
        names = list(raw)
    return [_normalise(n) for n in names]


def preprocess(path: Path) -> np.ndarray:
    """Decode -> center-crop largest square -> resize 224 -> [0,1] float32."""
    img = tf.io.read_file(str(path))
    img = tf.io.decode_image(img, channels=3, expand_animations=False)
    h, w = tf.shape(img)[0], tf.shape(img)[1]
    side = tf.minimum(h, w)
    img = tf.image.resize_with_crop_or_pad(img, side, side)
    img = tf.image.resize(img, (IMG_SIZE, IMG_SIZE), method="bilinear")
    img = tf.cast(img, tf.float32) / 255.0
    return img.numpy().astype(np.float32)[None, ...]


def run() -> None:
    labels = load_labels()
    label_set = set(labels)
    print(f"Loaded {len(labels)} class labels: {labels}")

    interp = tf.lite.Interpreter(model_path=str(MODEL_PATH))
    interp.allocate_tensors()
    in_idx = interp.get_input_details()[0]["index"]
    out_idx = interp.get_output_details()[0]["index"]

    confidences: list[float] = []
    correct: list[bool] = []
    skipped_classes: set[str] = set()
    n_images = 0

    for class_dir in sorted(Path(TEST_DIR).iterdir()):
        if not class_dir.is_dir():
            continue
        true_label = _normalise(class_dir.name)
        true_label = FOLDER_ALIASES.get(true_label, true_label)
        if true_label not in label_set:
            skipped_classes.add(class_dir.name)
            continue
        for img_path in class_dir.iterdir():
            if img_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            x = preprocess(img_path)
            interp.set_tensor(in_idx, x)
            interp.invoke()
            probs = interp.get_tensor(out_idx)[0]
            pred = labels[int(np.argmax(probs))]
            confidences.append(float(np.max(probs)))
            correct.append(pred == true_label)
            n_images += 1

    if skipped_classes:
        print(f"WARNING: folders with no matching label (add to FOLDER_ALIASES): "
              f"{sorted(skipped_classes)}")
    if n_images == 0:
        raise SystemExit(f"No images found under {TEST_DIR}. Check TEST_DIR / labels.")

    conf = np.array(confidences)
    corr = np.array(correct)
    overall_acc = float(corr.mean())
    print(f"\nEvaluated {n_images} images. Overall (no threshold) accuracy: "
          f"{overall_acc * 100:.2f}%")

    rows = []
    print(f"\n{'tau':>5} {'coverage':>10} {'sel.acc':>9} {'rejected':>9}")
    for tau in THRESHOLDS:
        covered = conf >= tau
        coverage = float(covered.mean())
        sel_acc = float(corr[covered].mean()) if covered.any() else float("nan")
        rows.append({"threshold": tau, "coverage": coverage,
                     "selective_accuracy": sel_acc, "rejected": 1.0 - coverage})
        print(f"{tau:>5.2f} {coverage * 100:>9.1f}% {sel_acc * 100:>8.2f}% "
              f"{(1 - coverage) * 100:>8.1f}%")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "threshold_sweep.json").write_text(
        json.dumps({"n_images": n_images, "overall_accuracy": overall_acc,
                    "sweep": rows}, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_DIR / 'threshold_sweep.json'}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        taus = [r["threshold"] for r in rows]
        plt.figure(figsize=(7, 4.5))
        plt.plot(taus, [r["selective_accuracy"] * 100 for r in rows],
                 "o-", label="Selective accuracy")
        plt.plot(taus, [r["coverage"] * 100 for r in rows],
                 "s--", label="Coverage")
        plt.axvline(0.60, color="grey", linestyle=":", label="Deployed threshold (0.60)")
        plt.xlabel("Confidence threshold τ")
        plt.ylabel("Percent")
        plt.title("Stage-3 risk–coverage trade-off")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(OUT_DIR / "threshold_sweep.png", dpi=150)
        print(f"Wrote {OUT_DIR / 'threshold_sweep.png'}")
    except ImportError:
        print("(matplotlib not installed — skipped the plot)")


if __name__ == "__main__":
    run()
