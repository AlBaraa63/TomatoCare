#!/usr/bin/env python3
"""
composite_eval.py — Composited-background field validation

Removes white backgrounds from PlantVillage TEST images and pastes
the leaves onto real-or-synthetic field backgrounds, then runs the
full TomatoCare cascade and reports accuracy.

What this tests:
  • If the model is using LEAF MORPHOLOGY  → accuracy stays high
  • If the model is using WHITE BACKGROUND → accuracy drops on composited images

White removal: pixels with R>220 AND G>220 AND B>220 are treated as
background — works reliably on PlantVillage's uniform studio backgrounds.

Backgrounds: attempts to download real farm/field photos from Wikimedia
Commons (free, no auth). Falls back to synthetic perlin-like colour noise
if downloads fail, so the script always runs offline.
"""
import io
import json
import random
import urllib.request
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, ImageFilter

# ── paths ────────────────────────────────────────────────────────────────────
ASSETS  = Path("/mnt/c/Users/POTATO/Desktop/TomatoCare/android/app/src/main/assets")
TEST_DIR = Path("/home/albaraa/tc_data/stage3_disease/test")

DISEASE = ["bacterial_spot", "early_blight", "healthy", "late_blight", "leaf_mold",
           "mosaic_virus", "powdery_mildew", "septoria_leaf_spot", "spider_mites",
           "target_spot", "yellow_leaf_curl_virus"]

IMG          = 224
CANVAS       = 320     # composite at 320×320 then center-crop to 224×224
SEED         = 42
N_PER_CLASS  = 15      # test images per disease class (165 total)
LEAF_IDX     = 0
TOMATO_IDX   = 1

rng = random.Random(SEED)
np.random.seed(SEED)

# ── background images ─────────────────────────────────────────────────────────
# Wikimedia Commons — tomato fields, garden foliage, soil — free & stable
BG_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Tomato_je.jpg/640px-Tomato_je.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Tomatinas.jpg/640px-Tomatinas.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Potato_plant.jpg/640px-Potato_plant.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Lettuce_field.jpg/640px-Lettuce_field.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Lecia_Sunflower_Field.jpg/640px-Lecia_Sunflower_Field.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Garden_blooms_in_the_spring.jpg/640px-Garden_blooms_in_the_spring.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Groundnut_field_Kadiri.JPG/640px-Groundnut_field_Kadiri.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Garden_soil.JPG/640px-Garden_soil.JPG",
]


def _synthetic_bg(seed: int) -> Image.Image:
    """Perlin-like RGB noise in foliage (green) or soil (brown) tones."""
    r = np.random.default_rng(seed)
    # choose palette
    if seed % 3 == 0:           # foliage green
        mu = np.array([55, 110, 40], dtype=np.float32)
    elif seed % 3 == 1:         # soil brown
        mu = np.array([120, 85,  45], dtype=np.float32)
    else:                       # dried grass / straw
        mu = np.array([160, 140, 60], dtype=np.float32)

    noise = r.normal(0, 35, (CANVAS, CANVAS, 3)).astype(np.float32)
    arr   = np.clip(mu + noise, 0, 255).astype(np.uint8)
    img   = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=4))
    return img


def load_backgrounds(n: int = 12) -> list:
    bgs = []
    for url in BG_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
            bgs.append(img)
            print(f"  [bg] ✓  {url.split('/')[-1]}")
        except Exception as e:
            print(f"  [bg] ✗  {url.split('/')[-1]}  ({e})")
    real_count = len(bgs)

    # fill remaining with synthetic
    while len(bgs) < n:
        bgs.append(_synthetic_bg(len(bgs)))
    print(f"  [bg] {real_count} real  +  {n - real_count} synthetic  =  {n} total")
    return bgs[:n]


# ── background removal ────────────────────────────────────────────────────────

def remove_white_bg(img_rgb: Image.Image, thresh: int = 220) -> Image.Image:
    """Convert uniform white background to alpha=0. Returns RGBA."""
    rgba = img_rgb.convert("RGBA")
    arr  = np.array(rgba)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    bg_mask = (r > thresh) & (g > thresh) & (b > thresh)

    # erode by 3px so edge fringe is removed (no scipy needed)
    for _ in range(3):
        bg_mask = (bg_mask
                   & np.roll(bg_mask,  1, axis=0)
                   & np.roll(bg_mask, -1, axis=0)
                   & np.roll(bg_mask,  1, axis=1)
                   & np.roll(bg_mask, -1, axis=1))

    arr[bg_mask, 3] = 0
    return Image.fromarray(arr)


def composite(leaf_rgba: Image.Image, bg: Image.Image) -> Image.Image:
    """Paste leaf (RGBA) onto field background, return RGB 224×224."""
    # resize background to canvas
    bg_c = bg.resize((CANVAS, CANVAS), Image.BILINEAR).convert("RGBA")

    # scale leaf to 78% of canvas — realistic hand-held distance
    leaf_size = int(CANVAS * 0.78)
    leaf_r    = leaf_rgba.resize((leaf_size, leaf_size), Image.BILINEAR)

    # random placement jitter (±8% of canvas) so model can't rely on fixed position
    jitter = int(CANVAS * 0.08)
    off_x  = (CANVAS - leaf_size) // 2 + rng.randint(-jitter, jitter)
    off_y  = (CANVAS - leaf_size) // 2 + rng.randint(-jitter, jitter)

    bg_c.paste(leaf_r, (off_x, off_y), leaf_r)

    # center-crop to 224×224 (same as model contract)
    s     = min(bg_c.size)
    left  = (bg_c.width  - s) // 2
    top   = (bg_c.height - s) // 2
    final = bg_c.crop((left, top, left + s, top + s)).resize((IMG, IMG), Image.BILINEAR)
    return final.convert("RGB")


# ── TFLite helpers ────────────────────────────────────────────────────────────

def interp(path: Path):
    it = tf.lite.Interpreter(model_path=str(path))
    it.allocate_tensors()
    return it


def run(it, x: np.ndarray) -> np.ndarray:
    i = it.get_input_details()[0]
    o = it.get_output_details()[0]
    it.set_tensor(i["index"], x)
    it.invoke()
    return it.get_tensor(o["index"])[0]


def pil_to_tensor(img: Image.Image) -> np.ndarray:
    arr = np.array(img.resize((IMG, IMG), Image.BILINEAR), dtype=np.float32) / 255.0
    return arr.reshape(1, IMG, IMG, 3)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("TomatoCare — Composited Background Field Validation")
    print("=" * 60)

    print("\n[1/4] Loading TFLite cascade...")
    leaf_it = interp(ASSETS / "stage1_leaf_float16.tflite")
    tom_it  = interp(ASSETS / "stage2_tomato_float16.tflite")
    dis_it  = interp(ASSETS / "stage3_disease_float16.tflite")

    print("\n[2/4] Loading backgrounds...")
    bgs = load_backgrounds(n=12)

    print("\n[3/4] Collecting test images...")
    items = []
    for cls_dir in sorted(TEST_DIR.iterdir()):
        if cls_dir.is_dir() and cls_dir.name in DISEASE:
            imgs = sorted(p for p in cls_dir.iterdir()
                          if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
            sampled = rng.sample(imgs, min(N_PER_CLASS, len(imgs)))
            for p in sampled:
                items.append((p, cls_dir.name))
    print(f"  {len(items)} images across {len(set(c for _, c in items))} classes")

    print("\n[4/4] Compositing and evaluating...")
    passed = correct = gate1_fail = gate2_fail = 0
    per_class = {}

    for idx, (p, true_cls) in enumerate(items):
        if idx % 20 == 0:
            print(f"  {idx}/{len(items)} ...", flush=True)

        pc = per_class.setdefault(true_cls, {"n": 0, "correct": 0,
                                              "g1_fail": 0, "g2_fail": 0})
        pc["n"] += 1

        # composite
        leaf_rgb  = Image.open(p).convert("RGB")
        leaf_rgba = remove_white_bg(leaf_rgb)
        bg        = rng.choice(bgs)
        comp      = composite(leaf_rgba, bg)
        x         = pil_to_tensor(comp)

        # stage 1
        if int(np.argmax(run(leaf_it, x))) != LEAF_IDX:
            gate1_fail += 1; pc["g1_fail"] += 1
            continue
        # stage 2
        if int(np.argmax(run(tom_it, x))) != TOMATO_IDX:
            gate2_fail += 1; pc["g2_fail"] += 1
            continue

        passed += 1
        pred = DISEASE[int(np.argmax(run(dis_it, x)))]
        if pred == true_cls:
            correct += 1
            pc["correct"] += 1

    # ── report ────────────────────────────────────────────────────────────────
    n = len(items)
    e2e_pct  = round(100 * correct / max(n, 1),      1)
    dis_pct  = round(100 * correct / max(passed, 1), 1)

    print(f"\n{'=' * 60}")
    print(f"  Total images          : {n}")
    print(f"  Gate-1 failures       : {gate1_fail}  ({100*gate1_fail/n:.1f}%)")
    print(f"  Gate-2 failures       : {gate2_fail}  ({100*gate2_fail/n:.1f}%)")
    print(f"  Passed both gates     : {passed}  ({100*passed/n:.1f}%)")
    print(f"  End-to-end correct    : {correct}/{n}  ({e2e_pct}%)")
    print(f"  Disease acc (passed)  : {correct}/{passed}  ({dis_pct}%)")
    print()
    print(f"  Compare vs PlantDoc field eval:")
    print(f"    Lab (PlantVillage) :  97.55% e2e  |  deployed ctrl model")
    print(f"    PlantDoc (real)    :  77.2%  e2e  |  deployed ctrl model")
    print(f"    Composited (this)  :  {e2e_pct}%  e2e  |  deployed ctrl model")
    print()
    print(f"  Per-class disease recall:")
    for k in sorted(per_class):
        pc = per_class[k]
        ratio = f"{pc['correct']}/{pc['n']}"
        bar   = "█" * pc["correct"] + "░" * (pc["n"] - pc["correct"])
        g_note = ""
        if pc["g1_fail"] or pc["g2_fail"]:
            g_note = f"  (gate drops: S1={pc['g1_fail']} S2={pc['g2_fail']})"
        print(f"    {k:26s}  {ratio:6s}  {bar}{g_note}")

    print("=" * 60)

    result = {
        "n": n, "gate1_fail": gate1_fail, "gate2_fail": gate2_fail,
        "passed": passed, "correct": correct,
        "e2e_pct": e2e_pct, "disease_pct": dis_pct,
        "per_class": {k: v for k, v in per_class.items()},
        "context": {
            "lab_e2e":      97.55,
            "plantdoc_e2e": 77.2,
            "composited_e2e": e2e_pct,
        }
    }
    out = Path("/tmp/composite_eval_result.json")
    out.write_text(json.dumps(result, indent=2))
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()
