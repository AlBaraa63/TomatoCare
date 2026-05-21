"""TREE / data — rebuild the tomato gate's negatives with DIVERSE species.

The hard-negative test exposed that a tomato gate trained on only potato +
pepper does NOT generalise: corn/grape/squash leaves leak through ~97-100%.
Fix: retrain the gate against the full spread of PlantVillage non-tomato
species so it learns "tomato vs ANY leaf", not "tomato vs potato/pepper".

We deliberately HOLD OUT grape + corn entirely (never train on them) so the
re-run of hard_negative_test.py gives an honest "unseen species" number.

This only rebuilds stage2_tomato/{train,val}/other_leaf. The tomato positives,
the leaf gate, and the disease classifier are left untouched.

Run inside the WSL venv:
    python ml/tree/enrich_tomato_negatives.py
"""
from __future__ import annotations

import os
import random
import shutil
from pathlib import Path

SEED = 42
VAL_FRAC = 0.15
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

SRC = Path("/mnt/c/Users/POTATO/Desktop/TomatoCare/ml/dataset/raw/"
           "plantvillage_full/plantvillage dataset/color")
CANON = Path.home() / "tc_data" / "_img" / "other_leaf_div"
STAGE2 = Path.home() / "tc_data" / "stage2_tomato"


def list_images(d: Path) -> list[Path]:
    return [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS]


def link_many(files, dest_dir: Path) -> int:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src in files:
        link = dest_dir / src.name
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(src.resolve(), link)
    return len(files)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-prefixes", default="Tomato,Grape,Corn",
                    help="Class-name prefixes kept OUT of training negatives. "
                         "Use 'Tomato' alone for the final deployable gate "
                         "(includes grape+corn).")
    args = ap.parse_args()
    exclude = tuple(s.strip() for s in args.exclude_prefixes.split(","))
    rng = random.Random(SEED)

    included, held_out = [], []
    all_files: list[Path] = []
    print("=== copying diverse non-tomato species to ext4 ===")
    for cls_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        if cls_dir.name.startswith(exclude):
            if not cls_dir.name.startswith("Tomato"):
                held_out.append(cls_dir.name)
            continue
        dest = CANON / cls_dir.name
        dest.mkdir(parents=True, exist_ok=True)
        imgs = list_images(cls_dir)
        for src in imgs:
            dst = dest / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            all_files.append(dst)
        included.append(f"{cls_dir.name}({len(imgs)})")
        print(f"  + {cls_dir.name:<45} {len(imgs)}")

    print(f"\nincluded {len(included)} classes, {len(all_files)} images")
    print(f"held out (unseen test): {held_out}")

    # Split + rebuild stage2 other_leaf symlinks.
    all_files = sorted(all_files, key=lambda p: p.name)
    rng.shuffle(all_files)
    n_val = int(round(len(all_files) * VAL_FRAC))
    val_files, train_files = all_files[:n_val], all_files[n_val:]

    for split, files in (("train", train_files), ("val", val_files)):
        d = STAGE2 / split / "other_leaf"
        if d.exists():
            shutil.rmtree(d)
        n = link_many(files, d)
        tomato_n = len(list((STAGE2 / split / "tomato").iterdir()))
        print(f"stage2/{split}: other_leaf={n}  tomato={tomato_n}")

    print("[done] tomato gate negatives enriched; retrain stage2_tomato next.")


if __name__ == "__main__":
    main()
