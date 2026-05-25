#!/usr/bin/env python3
"""
da_eval.py — Stage 2 of the test-time domain-adaptation experiment.

Reads the variants produced by da_segment.py (raw / white / white_crop) and
runs the deployed 3-stage cascade on each, reporting end-to-end accuracy and
per-class disease recall.

The question: does normalising a FIELD image toward the lab distribution
(segment leaf → white background) recover the accuracy lost to the domain gap?

    raw         baseline   (expected ≈ 77.2% e2e, the established PlantDoc number)
    white       leaf on white background, original framing
    white_crop  leaf cropped + centred on white square (most lab-like)

Run in the TF venv (tomatocare-wsl):
    /home/albaraa/.venvs/tomatocare-wsl/bin/python ml/tree/da_eval.py
"""
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

ASSETS = Path("/mnt/c/Users/POTATO/Desktop/TomatoCare/android/app/src/main/assets")
EXP    = Path("/tmp/da_exp")
IMG    = 224
LEAF_IDX, TOMATO_IDX = 0, 1

DISEASE = ["bacterial_spot", "early_blight", "healthy", "late_blight", "leaf_mold",
           "mosaic_virus", "powdery_mildew", "septoria_leaf_spot", "spider_mites",
           "target_spot", "yellow_leaf_curl_virus"]


def decode(path):
    raw = tf.io.read_file(str(path))
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    shape = tf.shape(img)
    s = tf.minimum(shape[0], shape[1])
    img = tf.image.resize_with_crop_or_pad(img, s, s)
    img = tf.image.resize(img, [IMG, IMG])
    return (tf.cast(img, tf.float32) / 255.0).numpy().reshape(1, IMG, IMG, 3).astype(np.float32)


def interp(path):
    it = tf.lite.Interpreter(model_path=str(path))
    it.allocate_tensors()
    return it


def run(it, x):
    i = it.get_input_details()[0]
    o = it.get_output_details()[0]
    it.set_tensor(i["index"], x)
    it.invoke()
    return it.get_tensor(o["index"])[0]


def evaluate(variant, manifest, leaf, tom, dis):
    vdir = EXP / variant
    n = len(manifest)
    passed = correct = g1 = g2 = 0
    per_class = {}
    for row in manifest:
        idx, true = row["idx"], row["label"]
        pc = per_class.setdefault(true, {"n": 0, "correct": 0})
        pc["n"] += 1
        x = decode(vdir / f"{idx:03d}.png")
        if int(np.argmax(run(leaf, x))) != LEAF_IDX:
            g1 += 1
            continue
        if int(np.argmax(run(tom, x))) != TOMATO_IDX:
            g2 += 1
            continue
        passed += 1
        if DISEASE[int(np.argmax(run(dis, x)))] == true:
            correct += 1
            pc["correct"] += 1
    return {
        "variant": variant, "n": n, "passed": passed, "correct": correct,
        "gate1_fail": g1, "gate2_fail": g2,
        "e2e_pct": round(100 * correct / max(n, 1), 1),
        "disease_pct": round(100 * correct / max(passed, 1), 1),
        "per_class": per_class,
    }


def main():
    manifest = json.loads((EXP / "manifest.json").read_text())
    seg_ok = sum(1 for r in manifest if r["seg_ok"])
    print(f"Loaded manifest: {len(manifest)} images, "
          f"segmentation ok on {seg_ok} ({100*seg_ok/len(manifest):.1f}%)\n")

    leaf = interp(ASSETS / "stage1_leaf_float16.tflite")
    tom  = interp(ASSETS / "stage2_tomato_float16.tflite")
    dis  = interp(ASSETS / "stage3_disease_float16.tflite")

    results = {}
    for variant in ("raw", "white", "white_crop"):
        r = evaluate(variant, manifest, leaf, tom, dis)
        results[variant] = r
        print(f"===== {variant.upper()} =====")
        print(f"  gates dropped : S1={r['gate1_fail']}  S2={r['gate2_fail']}")
        print(f"  passed        : {r['passed']}/{r['n']}")
        print(f"  end-to-end    : {r['e2e_pct']}%  ({r['correct']}/{r['n']})")
        print(f"  disease acc   : {r['disease_pct']}%  (on {r['passed']} passed)")
        print()

    # side-by-side per-class
    print("Per-class end-to-end recall (correct / n):")
    classes = sorted({c for r in results.values() for c in r["per_class"]})
    print(f"  {'class':26s} {'raw':>8s} {'white':>8s} {'white_crop':>11s}")
    for c in classes:
        cells = []
        for v in ("raw", "white", "white_crop"):
            pc = results[v]["per_class"].get(c, {"n": 0, "correct": 0})
            cells.append(f"{pc['correct']}/{pc['n']}")
        print(f"  {c:26s} {cells[0]:>8s} {cells[1]:>8s} {cells[2]:>11s}")

    print("\nSummary (end-to-end):")
    for v in ("raw", "white", "white_crop"):
        print(f"  {v:12s} {results[v]['e2e_pct']:5.1f}%")

    Path("/tmp/da_eval_result.json").write_text(json.dumps(results, indent=2))
    print("\nSaved → /tmp/da_eval_result.json")


if __name__ == "__main__":
    main()
