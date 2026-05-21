"""A3 — Offline augmentation (UAE-domain + real-world phone-shot).

Reads each split CSV, applies augmentations N times per image, and writes
the results to disk:

    dataset/augmented/train/<class>/<image>.jpg
    dataset/augmented/val/<class>/<image>.jpg   (light aug, see below)
    dataset/augmented/test/<class>/<image>.jpg  (light aug, see below)

Why offline (vs on-the-fly):
  - Capstone graders re-run training without our random seed; offline
    augmentation pins the exact set we report numbers on.
  - The augmented set is ~4x the original; even on CPU this is a one-time
    cost and saves wall-clock on every epoch.

Two augmentation stacks, applied in order, gated per-class:

  Stack 1 — UAE-domain (tomato classes only, indices 0..9):
    brightness × contrast × red-shift × Gaussian blur. These simulate UAE
    field conditions (peak solar irradiance, dust haze, heat shimmer) on
    PlantVillage's lab-clean images. They DO NOT make sense on a photo of
    a dog (the Tomato_NotALeaf class), so we skip them there.

  Stack 2 — real-world phone-shot (ALL classes including NotALeaf):
    rotation + flip + zoom + jpeg-recompress + motion blur + gamma +
    noise + perspective warp + random crop + cutout. These simulate
    artifacts of a real phone camera held by a human (compression, hand
    shake, exposure, off-center framing). This was the missing piece
    behind the "horrible prototype" — PlantVillage backgrounds are
    uniform, but real phone photos aren't, so the previous model never
    learned to handle realistic captures.

Val and test get a LIGHT version of Stack 2 only (JPEG re-encode + mild
gamma) so eval numbers reflect realistic phone capture rather than
inflated lab-clean accuracy.

Caching: per split, if the augmented folder has images, skip that split.
Delete dataset/augmented/<split>/ to force a re-run of just that split.
"""
from __future__ import annotations

import json
import random
import sys
from io import BytesIO
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


# ---------- UAE-domain primitives (tomato classes only) -----------------

def jitter_brightness(img: Image.Image, lo: float, hi: float) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(random.uniform(lo, hi))


def jitter_contrast(img: Image.Image, lo: float, hi: float) -> Image.Image:
    return ImageEnhance.Contrast(img).enhance(random.uniform(lo, hi))


def shift_red(img: Image.Image, lo: int, hi: int) -> Image.Image:
    arr = np.array(img).astype(np.int16)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return img
    arr[..., 0] = np.clip(arr[..., 0] + random.randint(lo, hi), 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def gaussian_blur(img: Image.Image, lo: float, hi: float) -> Image.Image:
    sigma = random.uniform(lo, hi)
    if sigma < 0.05:
        return img
    return img.filter(ImageFilter.GaussianBlur(radius=sigma))


# ---------- Real-world phone-shot primitives (all classes) --------------

def rotate(img: Image.Image, max_deg: float) -> Image.Image:
    return img.rotate(random.uniform(-max_deg, max_deg),
                      resample=Image.BILINEAR, fillcolor=(0, 0, 0))


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
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def jpeg_recompress(img: Image.Image, q_lo: int, q_hi: int) -> Image.Image:
    """Re-encode through a low-quality JPEG to inject phone-camera artifacts.

    PlantVillage was saved as high-quality JPEGs; real phone captures are
    typically q=70..85 with visible blocking, ringing, and chroma loss.
    """
    q = random.randint(q_lo, q_hi)
    buf = BytesIO()
    img.save(buf, "JPEG", quality=q)
    buf.seek(0)
    return Image.open(buf).convert("RGB").copy()


def motion_blur(img: Image.Image, max_kernel: int) -> Image.Image:
    """Approximate horizontal motion blur by averaging shifted copies.

    Pillow has no native motion-blur kernel, but a small box-blur along a
    random direction is a decent stand-in for hand-shake during capture.
    """
    if max_kernel <= 0:
        return img
    k = random.choice([0, 0, 3, 5, max_kernel])  # 2/5 probability of no blur
    if k < 3:
        return img
    arr = np.asarray(img).astype(np.float32)
    angle = random.choice([0, 45, 90, 135])
    shifted = np.zeros_like(arr)
    for i in range(k):
        offset = i - k // 2
        if angle == 0:
            shifted += np.roll(arr, offset, axis=1)
        elif angle == 90:
            shifted += np.roll(arr, offset, axis=0)
        else:
            shifted += np.roll(arr, (offset, offset if angle == 45 else -offset),
                               axis=(0, 1))
    shifted = (shifted / k).clip(0, 255).astype(np.uint8)
    return Image.fromarray(shifted)


def gamma_shift(img: Image.Image, lo: float, hi: float) -> Image.Image:
    g = random.uniform(lo, hi)
    arr = np.asarray(img).astype(np.float32) / 255.0
    arr = np.power(arr, g)
    return Image.fromarray((arr * 255.0).clip(0, 255).astype(np.uint8))


def gaussian_noise(img: Image.Image, std_lo: float, std_hi: float) -> Image.Image:
    std = random.uniform(std_lo, std_hi)
    if std < 0.5:
        return img
    arr = np.asarray(img).astype(np.float32)
    arr += np.random.normal(0, std, arr.shape)
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def perspective_warp(img: Image.Image, prob: float, strength: float) -> Image.Image:
    """Random perspective warp using PIL's QUAD transform.

    `strength` is a fraction of width/height the corners can wander.
    """
    if random.random() >= prob or strength <= 0:
        return img
    w, h = img.size
    dx = strength * w
    dy = strength * h
    quad = (
        random.uniform(0, dx),         random.uniform(0, dy),
        random.uniform(0, dx),         h - random.uniform(0, dy),
        w - random.uniform(0, dx),     h - random.uniform(0, dy),
        w - random.uniform(0, dx),     random.uniform(0, dy),
    )
    return img.transform(
        (w, h), Image.QUAD, quad, resample=Image.BILINEAR, fillcolor=(0, 0, 0))


def random_crop_off_center(img: Image.Image, max_frac: float) -> Image.Image:
    """Crop off up to max_frac of width/height from random sides, then resize back.

    Simulates the user not centering the subject perfectly.
    """
    if max_frac <= 0:
        return img
    w, h = img.size
    left = int(random.uniform(0, max_frac) * w)
    top = int(random.uniform(0, max_frac) * h)
    right = w - int(random.uniform(0, max_frac) * w)
    bottom = h - int(random.uniform(0, max_frac) * h)
    if right - left < 10 or bottom - top < 10:
        return img
    return img.crop((left, top, right, bottom)).resize((w, h), Image.BILINEAR)


def cutout(img: Image.Image, prob: float, max_size: int) -> Image.Image:
    """Apply a random black rectangle — forces the model to use spatial context."""
    if random.random() >= prob or max_size <= 0:
        return img
    w, h = img.size
    cw = random.randint(max_size // 2, max_size)
    ch = random.randint(max_size // 2, max_size)
    cx = random.randint(0, max(0, w - cw))
    cy = random.randint(0, max(0, h - ch))
    arr = np.asarray(img).copy()
    arr[cy:cy + ch, cx:cx + cw] = 0
    return Image.fromarray(arr)


# ---------- Composition ------------------------------------------------

def apply_uae_stack(img: Image.Image, cfg: dict) -> Image.Image:
    img = jitter_brightness(img, *cfg["brightness_range"])
    img = jitter_contrast(img, *cfg["contrast_range"])
    img = shift_red(img, *cfg["red_shift_range"])
    img = gaussian_blur(img, *cfg["blur_sigma_range"])
    return img


def apply_realworld_stack(img: Image.Image, cfg: dict) -> Image.Image:
    img = flip(img, cfg["hflip_prob"], cfg["vflip_prob"])
    img = rotate(img, cfg["rotation_degrees"])
    img = zoom(img, cfg["zoom_range"])
    img = random_crop_off_center(img, cfg["random_crop_max_off_center"])
    img = perspective_warp(img, cfg["perspective_warp_prob"],
                           cfg["perspective_warp_strength"])
    img = motion_blur(img, cfg["motion_blur_max_kernel"])
    img = gamma_shift(img, *cfg["gamma_range"])
    img = gaussian_noise(img, *cfg["gaussian_noise_std_range"])
    img = cutout(img, cfg["cutout_prob"], cfg["cutout_max_size"])
    img = jpeg_recompress(img, *cfg["jpeg_quality_range"])
    return img


def apply_light_stack(img: Image.Image, cfg: dict) -> Image.Image:
    """Val/test light pipeline — JPEG + mild gamma only, no geometric warps."""
    img = jpeg_recompress(img, *cfg["jpeg_quality_range"])
    img = gamma_shift(img, *cfg["gamma_range"])
    return img


def augment_train_image(img: Image.Image, is_tomato: bool,
                        uae_cfg: dict, rw_cfg: dict) -> Image.Image:
    if is_tomato:
        img = apply_uae_stack(img, uae_cfg)
    return apply_realworld_stack(img, rw_cfg)


# ---------- Main ------------------------------------------------------

def _process_split(split_name: str, df: pd.DataFrame, classes: list[str],
                   ood_class: str | None, aug_cfg: dict, img_size: int,
                   aug_dir: Path, aug_per_image: int) -> tuple[dict, list[dict]]:
    """Augment one split. Train uses Stack 1+2 with aug_per_image multipliers.

    Val/test apply ONE light pass — we want eval distributions to reflect
    realistic phone-shot conditions, but not to multiply the eval set size.

    Returns (per_class_counts, csv_rows). csv_rows is empty for train (the
    loader uses image_dataset_from_directory for train); for val/test it
    contains one row per produced file so the caller can rewrite the CSVs
    to point at the augmented images instead of the lab-clean originals.
    """
    split_dir = aug_dir / split_name
    split_dir.mkdir(parents=True, exist_ok=True)

    is_train = split_name == "train"
    is_val_or_test = split_name in {"val", "test"}
    light_cfg = aug_cfg.get("val_test_light") or {}
    light_enabled = is_val_or_test and light_cfg.get("enabled", False)

    per_class_after: dict[str, int] = {}
    csv_rows: list[dict] = []
    for cls in classes:
        cls_dir = split_dir / cls
        cls_dir.mkdir(parents=True, exist_ok=True)
        rows = df[df["label"] == cls]
        if len(rows) == 0:
            per_class_after[cls] = 0
            continue
        is_tomato = (cls != ood_class)
        class_index = classes.index(cls)
        produced = 0
        desc = f"{split_name}/{cls}"
        for _, row in tqdm(rows.iterrows(), total=len(rows),
                           desc=desc, leave=False):
            src = Path(row["filepath"])
            try:
                base = Image.open(src).convert("RGB").resize(
                    (img_size, img_size), Image.BILINEAR)
            except Exception as e:
                print(f"  >> SKIP corrupt: {src}  ({e})")
                continue

            if is_train:
                # Original (resized) + N augmented copies.
                orig_out = cls_dir / f"{src.stem}_orig.jpg"
                base.save(orig_out, "JPEG", quality=92)
                produced += 1
                for i in range(aug_per_image):
                    aug = augment_train_image(
                        base, is_tomato,
                        aug_cfg["uae"], aug_cfg["realworld"])
                    out = cls_dir / f"{src.stem}_aug{i}.jpg"
                    aug.save(out, "JPEG", quality=92)
                    produced += 1
            elif light_enabled:
                aug = apply_light_stack(base, light_cfg)
                out = cls_dir / f"{src.stem}_light.jpg"
                aug.save(out, "JPEG", quality=92)
                csv_rows.append({"filepath": str(out), "label": cls,
                                 "class_index": class_index})
                produced += 1
            else:
                # No augmentation — copy resized original.
                orig_out = cls_dir / f"{src.stem}.jpg"
                base.save(orig_out, "JPEG", quality=92)
                csv_rows.append({"filepath": str(orig_out), "label": cls,
                                 "class_index": class_index})
                produced += 1
        per_class_after[cls] = produced
        banner_step(f"AUG-{classes.index(cls):02d}",
                    f"{split_name} | {cls}",
                    originals=len(rows), produced=produced)

    return per_class_after, csv_rows


def main() -> None:
    banner_script("A3 Augmentation Pipeline (UAE + real-world)")
    set_seed(42)
    random.seed(42)
    np.random.seed(42)

    config = load_config()
    aug_cfg = config["augmentation"]
    root = project_root()
    splits_dir = root / config["paths"]["splits_dir"]
    aug_dir = root / config["paths"]["augmented_dir"]
    results_dir = root / config["paths"]["results_dir"]
    aug_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    log_path = results_dir / "augmentation_log.json"
    classes: list[str] = config["classes"]
    ood_class = (config.get("ood") or {}).get("class_name")
    img_size = config["img_size"]
    aug_per_image = aug_cfg["augmentations_per_image"]

    log: dict = {
        "augmentations_per_image": aug_per_image,
        "classes": classes,
        "ood_class": ood_class,
        "uae_params": aug_cfg["uae"],
        "realworld_params": aug_cfg["realworld"],
        "val_test_light": aug_cfg.get("val_test_light"),
        "per_split": {},
    }

    for split in ("train", "val", "test"):
        split_aug_dir = aug_dir / split
        # Cache check per-split: skip if any class has images already.
        existing = split_aug_dir.exists() and any(
            (split_aug_dir / cls).exists() and any((split_aug_dir / cls).iterdir())
            for cls in classes
        )
        if existing:
            print(f"  >> SKIP {split}: {split_aug_dir} already populated. "
                  "Delete to re-run.")
            continue

        csv_path = splits_dir / f"{split}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"{csv_path} not found. Run prepare_negatives + "
                "prepare_plantvillage first."
            )
        df = pd.read_csv(csv_path)
        banner_phase(f"Augmenting {split} split")
        per_class, csv_rows = _process_split(
            split, df, classes, ood_class, aug_cfg, img_size,
            aug_dir, aug_per_image,
        )
        log["per_split"][split] = per_class

        # For val/test: rewrite the CSV to point at the augmented files so
        # build_split_dataset evaluates on phone-shot-like images rather than
        # lab-clean originals. Train uses image_dataset_from_directory and
        # doesn't need a rewritten CSV.
        if split in {"val", "test"} and csv_rows:
            pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
            banner_step(f"CSV-{split.upper()}", f"{split}.csv rewritten",
                        rows=len(csv_rows), path=str(csv_path))

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    banner_step("LOG-01", "Augmentation log saved", path=str(log_path))


if __name__ == "__main__":
    main()
