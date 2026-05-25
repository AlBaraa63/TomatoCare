"""TREE / data — background suppression via MobileSAM zero-shot leaf masking.

Why: a classifier trained on lab images learns lab *background* cues (clean,
uniform) that don't exist in UAE field photos, so it transfers badly. If we
blank the background during training, the model is forced onto the LEAF itself
(lesions, colour, texture) and generalises far better to cluttered real photos.

How: zero-shot segmentation with MobileSAM (vit_t, ~39 MB) — reused straight
from the sibling F-UNet repo (it already ships the weights + package). Training
photos are leaf-centred, so we prompt SAM with the image-centre point plus a
generous centre box, take the best-scoring mask whose area is a sane fraction
of the frame, and write a background-suppressed copy (black / blur / mean).

This is a TRAINING-TIME step only — nothing changes on-device. After running it,
fold the suppressed images into the stage2/stage3 farms (additive, like
integrate_plantdoc.py) and retrain so the model sees both raw and
background-suppressed views.

Run in a venv that has torch (see setup_seg_env.sh):
    python ml/tree/segment_leaves.py --input <dir-of-class-folders> \
        --output <out-dir> --bg-mode blur --limit 0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# MobileSAM lives in the F-UNet repo — reuse weights + package, don't duplicate.
MOBILE_SAM_DIR = Path(
    "/mnt/c/Users/POTATO/Desktop/F-UNet/src/other_architectures/MobileSAM")
CKPT = MOBILE_SAM_DIR / "weights" / "mobile_sam.pt"
MODEL_TYPE = "vit_t"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def load_predictor(device: str):
    import torch  # imported here so --help works without torch installed
    sys.path.append(str(MOBILE_SAM_DIR))
    from mobile_sam import sam_model_registry, SamPredictor
    if not CKPT.exists():
        sys.exit(f"MobileSAM checkpoint not found: {CKPT}")
    sam = sam_model_registry[MODEL_TYPE](checkpoint=str(CKPT))
    sam.to(device=device)
    sam.eval()
    return SamPredictor(sam)


def leaf_mask(predictor, img_rgb: np.ndarray,
              min_area: float, max_area: float) -> np.ndarray | None:
    """Best central-leaf mask for a leaf-centred photo, or None if unsure."""
    h, w = img_rgb.shape[:2]
    predictor.set_image(img_rgb)
    point = np.array([[w // 2, h // 2]])
    label = np.array([1])
    box = np.array([w * 0.08, h * 0.08, w * 0.92, h * 0.92])
    masks, scores, _ = predictor.predict(
        point_coords=point, point_labels=label,
        box=box, multimask_output=True)

    best, best_score = None, -1.0
    for m, s in zip(masks, scores):
        frac = float(m.mean())
        if min_area <= frac <= max_area and s > best_score:
            best, best_score = m, float(s)
    if best is None:  # fallback: largest mask, still bounded by max_area
        for m, s in zip(masks, scores):
            frac = float(m.mean())
            if frac <= max_area and (best is None or m.sum() > best.sum()):
                best = m
    return best.astype(bool) if best is not None else None


def suppress(img_rgb: np.ndarray, mask: np.ndarray, mode: str) -> np.ndarray:
    out = img_rgb.copy()
    bg = ~mask
    if mode == "black":
        out[bg] = 0
    elif mode == "mean":
        out[bg] = img_rgb[mask].mean(axis=0).astype(img_rgb.dtype) if mask.any() else 0
    elif mode == "blur":
        blurred = np.asarray(
            Image.fromarray(img_rgb).filter(ImageFilter.GaussianBlur(14)))
        out[bg] = blurred[bg]
    else:
        sys.exit(f"unknown --bg-mode {mode}")
    return out


def images_under(d: Path) -> list[Path]:
    return [p for p in sorted(d.rglob("*"))
            if p.is_file() and p.suffix.lower() in IMG_EXTS]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True,
                    help="Dir of class subfolders (e.g. stage3_disease/train).")
    ap.add_argument("--output", required=True,
                    help="Output dir; class structure is mirrored.")
    ap.add_argument("--bg-mode", default="blur", choices=["blur", "black", "mean"])
    ap.add_argument("--limit", type=int, default=0,
                    help="Max images per class folder (0 = all).")
    ap.add_argument("--min-area", type=float, default=0.04)
    ap.add_argument("--max-area", type=float, default=0.97)
    ap.add_argument("--device", default=None, help="cuda / cpu (auto by default).")
    args = ap.parse_args()

    import torch
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[seg] device={device}  bg-mode={args.bg_mode}")
    predictor = load_predictor(device)

    in_root, out_root = Path(args.input), Path(args.output)
    class_dirs = sorted(p for p in in_root.iterdir() if p.is_dir())
    if not class_dirs:           # flat folder of images
        class_dirs = [in_root]

    total_ok = total_skip = 0
    for cdir in class_dirs:
        files = images_under(cdir)
        if args.limit:
            files = files[:args.limit]
        rel = cdir.relative_to(in_root) if cdir != in_root else Path(".")
        odir = out_root / rel
        odir.mkdir(parents=True, exist_ok=True)
        ok = skip = 0
        for f in files:
            try:
                img = np.asarray(Image.open(f).convert("RGB"))
                m = leaf_mask(predictor, img, args.min_area, args.max_area)
                if m is None:
                    skip += 1
                    continue
                out = suppress(img, m, args.bg_mode)
                Image.fromarray(out).save(odir / f"seg_{f.name}")
                ok += 1
            except Exception:
                skip += 1
        total_ok += ok
        total_skip += skip
        print(f"  {rel}: {ok} suppressed, {skip} skipped")

    print(f"\n[done] {total_ok} background-suppressed images written to {out_root} "
          f"({total_skip} skipped). Fold into stage2/stage3 train splits and retrain.")


if __name__ == "__main__":
    main()
