"""A3 — UAE-domain augmentation pipeline (offline, write-to-disk).

Reads train.csv, applies UAE-specific augmentations N times per image, and
writes the results to dataset/augmented/train/<class_name>/. Val and test
are NOT augmented — they must remain a clean estimate of generalisation.

Why offline (vs on-the-fly):
  - Capstone graders may re-run training without our random seed; offline
    augmentation pins the exact training set we report numbers on.
  - The augmented set is ~4x the original; even on a CPU this is a one-time
    cost and saves wall-clock on every training epoch.

Why these specific augmentations:
  - Standard flips/rotations: orientation invariance (table stakes).
  - Brightness [0.6,1.4]: UAE peak solar irradiance bleaches highlights;
    PlantVillage was shot under controlled lab lighting.
  - Contrast [0.7,1.3]: same lighting-shift reason.
  - Red-channel shift +10..+25: dust haze adds a warm orange cast to outdoor
    UAE photos; shifting R up simulates this without destroying lesion hue.
  - Gaussian blur sigma 0..1.5: heat shimmer at >40C distorts focus.
  - Zoom up to 20%: scale invariance for hand-held capture distance.

Caching: if dataset/augmented/train/ already contains images, skip entirely.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402


def banner_script(purpose: str) -> None:
    print("##############################################################")
    print(f"  TomatoCare — {purpose}")
    print(f"  Device : cpu")
    print(f"  Seed   : 42")
    print("##############################################################")


def banner_phase(name: str) -> None:
    print("==============================================================")
    print(f"  PHASE: {name}")
    print("==============================================================")


def banner_step(step_id: str, desc: str, **params) -> None:
    print("--------------------------------------------------------------")
    print(f"  [{step_id}] {desc}")
    if params:
        print("  " + "  |  ".join(f"{k}: {v}" for k, v in params.items()))
    print("--------------------------------------------------------------")


def jitter_brightness(img: Image.Image, lo: float, hi: float) -> Image.Image:
    factor = random.uniform(lo, hi)
    return ImageEnhance.Brightness(img).enhance(factor)


def jitter_contrast(img: Image.Image, lo: float, hi: float) -> Image.Image:
    factor = random.uniform(lo, hi)
    return ImageEnhance.Contrast(img).enhance(factor)


def shift_red(img: Image.Image, lo: int, hi: int) -> Image.Image:
    # Add a uniform offset to the R channel only, clipped to [0,255].
    arr = np.array(img).astype(np.int16)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return img
    shift = random.randint(lo, hi)
    arr[..., 0] = np.clip(arr[..., 0] + shift, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def blur(img: Image.Image, lo: float, hi: float) -> Image.Image:
    sigma = random.uniform(lo, hi)
    if sigma < 0.05:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=sigma))


def rotate(img: Image.Image, max_deg: float) -> Image.Image:
    deg = random.uniform(-max_deg, max_deg)
    return img.rotate(deg, resample=Image.BILINEAR,
                      fillcolor=(0, 0, 0))


def flip(img: Image.Image, hprob: float, vprob: float) -> Image.Image:
    if random.random() < hprob:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if random.random() < vprob:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


def zoom(img: Image.Image, max_zoom: float) -> Image.Image:
    if max_zoom <= 0:
        return img
    factor = 1.0 + random.uniform(0.0, max_zoom)
    w, h = img.size
    new_w, new_h = int(w * factor), int(h * factor)
    img = img.resize((new_w, new_h), Image.BILINEAR)
    # Center crop back to original size.
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def augment_once(img: Image.Image, aug: dict) -> Image.Image:
    # Compose UAE-domain augmentations in a fixed order; randomness lives
    # in the per-step parameters, not the order.
    img = flip(img, aug["hflip_prob"], aug["vflip_prob"])
    img = rotate(img, aug["rotation_degrees"])
    img = zoom(img, aug["zoom_range"])
    img = jitter_brightness(img, *aug["brightness_range"])
    img = jitter_contrast(img, *aug["contrast_range"])
    img = shift_red(img, *aug["red_shift_range"])
    img = blur(img, *aug["blur_sigma_range"])
    return img


def main() -> None:
    banner_script("A3 UAE Augmentation Pipeline")
    set_seed(42)
    random.seed(42)

    config = load_config()
    aug = config["augmentation"]
    root = project_root()
    splits_dir = root / config["paths"]["splits_dir"]
    aug_dir = root / config["paths"]["augmented_dir"] / "train"
    results_dir = root / config["paths"]["results_dir"]
    aug_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    log_path = results_dir / "augmentation_log.json"

    # Cache check — any class folder with images counts as already done.
    existing = any(
        (aug_dir / cls).exists() and any((aug_dir / cls).iterdir())
        for cls in config["classes"]
    )
    if existing and log_path.exists():
        print(f"  >> SKIP: augmented set exists at {aug_dir}. Delete to re-run.")
        with open(log_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    train_csv = splits_dir / "train.csv"
    if not train_csv.exists():
        raise FileNotFoundError(
            f"{train_csv} not found. Run prepare_plantvillage.py first."
        )
    df = pd.read_csv(train_csv)

    banner_phase("UAE Augmentation")
    aug_per_image = aug["augmentations_per_image"]
    log = {"per_class_before": {}, "per_class_after": {},
           "augmentations_per_image": aug_per_image, "params": aug}

    img_size = config["img_size"]

    for cls in config["classes"]:
        cls_dir = aug_dir / cls
        cls_dir.mkdir(parents=True, exist_ok=True)
        rows = df[df["label"] == cls]
        log["per_class_before"][cls] = int(len(rows))
        banner_step(f"AUG-{config['classes'].index(cls):02d}", cls,
                    originals=len(rows),
                    target_after=len(rows) * (1 + aug_per_image))

        produced = 0
        for _, row in tqdm(rows.iterrows(), total=len(rows),
                           desc=cls, leave=False):
            src = Path(row["filepath"])
            try:
                base = Image.open(src).convert("RGB").resize(
                    (img_size, img_size), Image.BILINEAR)
            except Exception as e:
                print(f"  >> SKIP corrupt image: {src}  ({e})")
                continue

            # Write the original (resized) as the canonical copy.
            orig_out = cls_dir / f"{src.stem}_orig.jpg"
            base.save(orig_out, "JPEG", quality=92)
            produced += 1

            for i in range(aug_per_image):
                a = augment_once(base, aug)
                out = cls_dir / f"{src.stem}_aug{i}.jpg"
                a.save(out, "JPEG", quality=92)
                produced += 1

        log["per_class_after"][cls] = produced

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    banner_step("LOG-01", "Augmentation log saved", path=str(log_path))


if __name__ == "__main__":
    main()
