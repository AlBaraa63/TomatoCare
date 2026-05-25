#!/usr/bin/env python3
"""
da_segment.py — Stage 1 of the test-time domain-adaptation experiment.

Hypothesis (AlBaraa's idea): the model was trained on lab images (uniform light
backgrounds). Rather than teaching it field robustness — which failed three
times (heavy aug, segmentation fold-in, GAN) — transform each FIELD image at
inference time to match the TRAINING distribution: segment the leaf and put it
on a white background.

This script segments PlantDoc tomato field photos with MobileSAM and writes
three parallel versions of each image plus a manifest:
    raw         : field image, resized only (the 77.2% baseline)
    white       : background → white, original framing kept
    white_crop  : leaf cropped to its bounding box and centred on a white
                  square — the closest match to a PlantVillage macro shot

Run in the torch venv (seg-wsl):
    /home/albaraa/.venvs/seg-wsl/bin/python ml/tree/da_segment.py
Stage 2 (da_eval.py) then runs the cascade on each version.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MOBILE_SAM_DIR = Path(
    "/mnt/c/Users/POTATO/Desktop/F-UNet/src/other_architectures/MobileSAM")
CKPT = MOBILE_SAM_DIR / "weights" / "mobile_sam.pt"

H   = Path("/home/albaraa")
PD  = H / "tc_data" / "_img" / "plantdoc"
OUT = Path("/tmp/da_exp")

TOMATO_MAP = {
    "Tomato_leaf": "healthy",
    "Tomato_Early_blight_leaf": "early_blight",
    "Tomato_leaf_bacterial_spot": "bacterial_spot",
    "Tomato_leaf_late_blight": "late_blight",
    "Tomato_leaf_mosaic_virus": "mosaic_virus",
    "Tomato_leaf_yellow_virus": "yellow_leaf_curl_virus",
    "Tomato_mold_leaf": "leaf_mold",
    "Tomato_Septoria_leaf_spot": "septoria_leaf_spot",
    "Tomato_two_spotted_spider_mites_leaf": "spider_mites",
}
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def load_predictor():
    import torch
    sys.path.append(str(MOBILE_SAM_DIR))
    from mobile_sam import sam_model_registry, SamPredictor
    if not CKPT.exists():
        sys.exit(f"MobileSAM checkpoint missing: {CKPT}")
    sam = sam_model_registry["vit_t"](checkpoint=str(CKPT))
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    sam.to(device=dev)
    sam.eval()
    print(f"[seg] MobileSAM vit_t on {dev}")
    return SamPredictor(sam)


def leaf_mask(predictor, img, min_area=0.04, max_area=0.97):
    """Best central-leaf mask, or None if no plausible mask."""
    h, w = img.shape[:2]
    predictor.set_image(img)
    point = np.array([[w // 2, h // 2]])
    label = np.array([1])
    box = np.array([w * 0.05, h * 0.05, w * 0.95, h * 0.95])
    masks, scores, _ = predictor.predict(
        point_coords=point, point_labels=label, box=box, multimask_output=True)
    best, best_s = None, -1.0
    for m, s in zip(masks, scores):
        frac = float(m.mean())
        if min_area <= frac <= max_area and s > best_s:
            best, best_s = m, float(s)
    if best is None:
        for m, s in zip(masks, scores):
            if float(m.mean()) <= max_area and (best is None or m.sum() > best.sum()):
                best = m
    return best.astype(bool) if best is not None else None


def to_white(img, mask):
    out = img.copy()
    out[~mask] = 255
    return out


def to_white_crop(img, mask, pad=0.08):
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return to_white(img, mask)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    h, w = img.shape[:2]
    py, px = int((y1 - y0) * pad), int((x1 - x0) * pad)
    y0, y1 = max(0, y0 - py), min(h, y1 + py)
    x0, x1 = max(0, x0 - px), min(w, x1 + px)
    crop = img[y0:y1, x0:x1].copy()
    cmask = mask[y0:y1, x0:x1]
    crop[~cmask] = 255
    ch, cw = crop.shape[:2]
    side = max(ch, cw)
    canvas = np.full((side, side, 3), 255, np.uint8)
    oy, ox = (side - ch) // 2, (side - cw) // 2
    canvas[oy:oy + ch, ox:ox + cw] = crop
    return canvas


def collect_items():
    items = []
    for split in ("test",):                       # test split only (held out)
        root = PD / split
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if d.is_dir() and d.name in TOMATO_MAP:
                for p in sorted(d.iterdir()):
                    if p.suffix.lower() in EXTS:
                        items.append((p, TOMATO_MAP[d.name]))
    return items


def main():
    for sub in ("raw", "white", "white_crop"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    predictor = load_predictor()
    items = collect_items()
    print(f"[seg] {len(items)} PlantDoc tomato test images")

    manifest = []
    seg_ok = 0
    for idx, (p, label) in enumerate(items):
        try:
            img = np.asarray(Image.open(p).convert("RGB"))
        except Exception as e:
            print(f"  [skip] {p.name}: {e}")
            continue

        # raw
        Image.fromarray(img).save(OUT / "raw" / f"{idx:03d}.png")

        # segmented variants
        m = leaf_mask(predictor, img)
        ok = m is not None
        if ok:
            seg_ok += 1
            Image.fromarray(to_white(img, m)).save(OUT / "white" / f"{idx:03d}.png")
            Image.fromarray(to_white_crop(img, m)).save(OUT / "white_crop" / f"{idx:03d}.png")
        else:
            # segmentation failed → fall back to raw for both (honest: no transform)
            Image.fromarray(img).save(OUT / "white" / f"{idx:03d}.png")
            Image.fromarray(img).save(OUT / "white_crop" / f"{idx:03d}.png")

        manifest.append({"idx": idx, "label": label, "seg_ok": ok,
                         "src": str(p)})
        if idx % 20 == 0:
            print(f"  {idx}/{len(items)} (seg_ok={seg_ok})", flush=True)

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n[done] {len(manifest)} images, segmentation succeeded on "
          f"{seg_ok}/{len(manifest)} ({100*seg_ok/max(len(manifest),1):.1f}%)")
    print(f"       variants in {OUT}/  →  run da_eval.py next")


if __name__ == "__main__":
    main()
