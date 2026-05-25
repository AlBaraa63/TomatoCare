"""TREE / predict — run the full decision tree on any image(s).

Mirrors exactly what the Android app will do, using the exported float16
TFLite models:

    image -> Stage1 leaf gate -> Stage2 tomato gate -> Stage3 diagnosis

Output per image is the human verdict:
    NOT A LEAF (retake)            if the leaf gate rejects
    NOT A TOMATO LEAF (retake)     if the tomato gate rejects
    <disease> (conf)               otherwise, with a LOW-CONFIDENCE flag if < 0.60

Usage inside the WSL venv (paths under /mnt/c/... point at your Windows files):

    python ml/tree/predict.py "/mnt/c/Users/POTATO/Desktop/myleaf.jpg"
    python ml/tree/predict.py /some/folder --limit 10
    python ml/tree/predict.py img1.jpg img2.jpg img3.jpg
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

IMG = 224
TFLITE = Path.home() / "tc_data" / "tflite"
MODELS = Path.home() / "tc_data" / "models"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


def interp(name: str) -> tf.lite.Interpreter:
    it = tf.lite.Interpreter(model_path=str(TFLITE / name))
    it.allocate_tensors()
    return it


def run(it: tf.lite.Interpreter, x: np.ndarray) -> np.ndarray:
    inp = it.get_input_details()[0]
    out = it.get_output_details()[0]
    it.set_tensor(inp["index"], x)
    it.invoke()
    return it.get_tensor(out["index"])[0]


def meta_names(stage: str) -> list[str]:
    return json.loads((MODELS / f"{stage}.meta.json").read_text())["class_names"]


def preprocess(p: Path) -> np.ndarray:
    im = Image.open(p).convert("RGB")
    # center-crop to the largest square (matches crop_to_aspect_ratio in
    # training), then resize -> no aspect-ratio distortion.
    w, h = im.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    im = im.crop((left, top, left + s, top + s)).resize((IMG, IMG))
    return np.expand_dims(np.asarray(im, np.float32) / 255.0, 0)


def gather(paths: list[str], limit: int) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            found = sorted(q for q in p.rglob("*") if q.suffix.lower() in IMG_EXTS)
            files += found[:limit] if limit else found
        elif p.is_file():
            files.append(p)
    return files


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="Image file(s) or folder(s).")
    ap.add_argument("--conf", type=float, default=0.60,
                    help="Low-confidence threshold for the diagnosis (default 0.60).")
    ap.add_argument("--limit", type=int, default=0,
                    help="Max images per folder (0 = all).")
    args = ap.parse_args()

    leaf, tom, dis = (interp("stage1_leaf_float16.tflite"),
                      interp("stage2_tomato_float16.tflite"),
                      interp("stage3_disease_float16.tflite"))
    ln, tn, dn = meta_names("stage1_leaf"), meta_names("stage2_tomato"), meta_names("stage3_disease")
    LEAF, TOMATO = ln.index("leaf"), tn.index("tomato")

    files = gather(args.paths, args.limit)
    if not files:
        print("No images found.")
        return

    for f in files:
        try:
            x = preprocess(f)
        except Exception as e:
            print(f"{f.name:40} SKIP (unreadable: {e})")
            continue

        pl = run(leaf, x)
        if int(pl.argmax()) != LEAF:
            print(f"{f.name:40} NOT A LEAF        (p={pl[ln.index('not_leaf')]:.2f})  -> retake")
            continue
        pt = run(tom, x)
        if int(pt.argmax()) != TOMATO:
            print(f"{f.name:40} NOT A TOMATO LEAF (p_other={pt[tn.index('other_leaf')]:.2f})  -> retake")
            continue
        pd = run(dis, x)
        top = int(pd.argmax())
        conf = float(pd[top])
        flag = "  [LOW CONFIDENCE <0.60]" if conf < args.conf else ""
        print(f"{f.name:40} {dn[top]}  ({conf:.2f}){flag}")


if __name__ == "__main__":
    main()
