"""TREE / data — remove images TensorFlow cannot decode.

image_dataset_from_directory feeds files to tf.io.decode_image, which only
accepts JPEG / PNG / GIF / BMP. Kaggle dumps routinely contain a few files
that are truncated, or are actually WEBP/TIFF/HTML saved with a .jpg name —
those crash training mid-epoch with:
    InvalidArgumentError: Unknown image file format.

We pre-scan the canonical ext4 copies with PIL (fast), delete anything that
isn't a loadable JPEG/PNG/GIF/BMP, then drop the now-dangling symlinks from
the stage farm so the loaders never see them.

Run inside the WSL venv:
    python ml/tree/clean_images.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = False  # we WANT truncated files to fail
OK_FORMATS = {"JPEG", "PNG", "GIF", "BMP"}

ROOT = Path.home() / "tc_data"
SCAN_ROOTS = [ROOT / "_img", ROOT / "raw" / "notleaf"]
STAGE_DIRS = [ROOT / "stage1_leaf", ROOT / "stage2_tomato", ROOT / "stage3_disease"]


def is_bad(p: Path) -> bool:
    try:
        with Image.open(p) as im:
            fmt = im.format
            im.load()                 # forces full decode -> catches truncation
            im.convert("RGB")
        return fmt not in OK_FORMATS
    except Exception:
        return True


def main() -> None:
    bad = []
    scanned = 0
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".bmp"}:
                scanned += 1
                if is_bad(p):
                    bad.append(p)
    print(f"scanned {scanned} images; found {len(bad)} bad")
    for p in bad:
        print("  bad:", p)
        p.unlink()

    # Drop dangling symlinks (targets we just deleted) from the stage farm.
    dangling = 0
    for sd in STAGE_DIRS:
        if not sd.exists():
            continue
        for link in sd.rglob("*"):
            if link.is_symlink() and not link.exists():
                link.unlink()
                dangling += 1
    print(f"[done] removed {len(bad)} corrupt files, {dangling} dangling symlinks")


if __name__ == "__main__":
    main()
