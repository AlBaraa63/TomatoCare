"""TREE / data — fold PlantDoc FIELD images into the tomato gate + disease sets.

Why: every negative the tomato gate saw so far was a PlantVillage LAB image
(clean background), while its tomato positives included field photos. The gate
could therefore cheat on photo STYLE ("lab-looking = other plant, field-looking
= tomato") instead of leaf identity — which is exactly why real-world photos of
other plants get called tomato. PlantDoc is real field photos (cluttered
backgrounds, phone quality), so:

  * PlantDoc NON-tomato leaves  -> tomato-gate negatives  (kills the shortcut)
  * PlantDoc tomato leaves      -> tomato-gate positives + disease classes

Additive + idempotent: copies PlantDoc to ext4 and appends symlinks into the
existing stage2 / stage3 farms (PlantDoc train -> train split, test -> val
split). The held-out tomato TEST set is left untouched, so test accuracy stays
comparable. After this: run clean_images.py, then retrain stage2 + stage3.

Run inside the WSL venv:
    python ml/tree/integrate_plantdoc.py
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
PD = Path("/mnt/c/Users/POTATO/Desktop/TomatoCare/ml/dataset/raw/plantdoc")
CANON = Path.home() / "tc_data" / "_img" / "plantdoc"
S2 = Path.home() / "tc_data" / "stage2_tomato"
S3 = Path.home() / "tc_data" / "stage3_disease"

# PlantDoc tomato class folder -> our canonical disease key.
# (PlantDoc has no target_spot or powdery_mildew tomato class — those stay
#  lab-only, which is fine.)
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


def images(d: Path) -> list[Path]:
    return [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS]


def link(src: Path, dest_dir: Path, tag: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    l = dest_dir / f"pd_{tag}_{src.name}"
    if l.exists() or l.is_symlink():
        l.unlink()
    os.symlink(src.resolve(), l)


def main() -> None:
    counts: dict[str, int] = {}
    for split in ("train", "test"):
        stage_split = "train" if split == "train" else "val"
        sdir = PD / split
        if not sdir.is_dir():
            continue
        for cls_dir in sorted(p for p in sdir.iterdir() if p.is_dir()):
            name = cls_dir.name
            files = images(cls_dir)
            if not files:
                continue
            cdst = CANON / split / name
            cdst.mkdir(parents=True, exist_ok=True)
            copied = []
            for s in files:
                d = cdst / s.name
                if not d.exists():
                    try:
                        shutil.copy2(s, d)
                    except Exception:
                        continue
                copied.append(d)

            if name.startswith("Tomato"):
                for d in copied:
                    link(d, S2 / stage_split / "tomato", name)
                key = TOMATO_MAP.get(name)
                if key:
                    for d in copied:
                        link(d, S3 / stage_split / key, name)
                counts[f"{split}/{name} -> tomato"
                       + (f" + disease:{key}" if key else " (no disease map)")] = len(copied)
            else:
                for d in copied:
                    link(d, S2 / stage_split / "other_leaf", name)
                counts[f"{split}/{name} -> other_leaf"] = len(copied)

    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print(f"\n[done] PlantDoc folded in ({sum(counts.values())} field images). "
          "Run clean_images.py, then retrain stage2 + stage3.")


if __name__ == "__main__":
    main()
