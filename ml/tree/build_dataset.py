"""TREE / data — stage raw downloads into the 3 training problems.

Pipeline shape (the professor's decision tree):

    Stage 1  leaf gate    : leaf        vs  not_leaf
    Stage 2  tomato gate   : tomato      vs  other_leaf
    Stage 3  diagnose       : 11 tomato disease/health classes

Two-step staging, chosen for GPU-feed speed + zero wasted disk:

  1. CANONICAL COPY — every raw image is copied ONCE from the Windows mount
     (/mnt/c, slow 9P reads) onto the Linux ext4 disk under <dest>/_img.
     Training then reads from ext4, so the RTX 4070 isn't starved by /mnt/c.

  2. SYMLINK FARM — each stage/split/class folder is filled with symlinks
     pointing back at the canonical ext4 copies. An image that is a Stage-3
     'late_blight' sample, a Stage-2 'tomato' sample, and a Stage-1 'leaf'
     sample exists on disk once but is linked from all three. Keras'
     image_dataset_from_directory follows the symlinks transparently.

Splits (deterministic, seed=42):
  - tomato20k/train  -> stage train/val (stratified 85/15 per class)
  - tomato20k/valid  -> stage TEST (held out; never seen in training)
  - other_leaf, not_leaf -> 85/15 train/val

Idempotent: re-running skips the canonical copy when files already exist and
rebuilds the (cheap) symlink farm from scratch.

Run inside the WSL venv:
    python ml/tree/build_dataset.py
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
from pathlib import Path

SEED = 42
IMG_EXTS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}

# tomato20k folder name -> canonical app class key (lowercase_snake_case,
# matching the Android labels contract).
TOMATO_CLASS_MAP = {
    "Bacterial_spot": "bacterial_spot",
    "Early_blight": "early_blight",
    "healthy": "healthy",
    "Late_blight": "late_blight",
    "Leaf_Mold": "leaf_mold",
    "powdery_mildew": "powdery_mildew",
    "Septoria_leaf_spot": "septoria_leaf_spot",
    "Spider_mites Two-spotted_spider_mite": "spider_mites",
    "Target_Spot": "target_spot",
    "Tomato_mosaic_virus": "mosaic_virus",
    "Tomato_Yellow_Leaf_Curl_Virus": "yellow_leaf_curl_virus",
}


def list_images(d: Path) -> list[Path]:
    if not d.is_dir():
        return []
    return [p for p in d.iterdir() if p.is_file() and p.suffix in IMG_EXTS]


def copy_into(files: list[Path], dest: Path) -> list[Path]:
    """Copy files into dest (ext4). Idempotent per-file. Returns dest paths."""
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    for src in files:
        dst = dest / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
        out.append(dst)
    return out


def split_train_val(files: list[Path], val_frac: float, rng: random.Random):
    files = sorted(files, key=lambda p: p.name)
    rng.shuffle(files)
    n_val = int(round(len(files) * val_frac))
    return files[n_val:], files[:n_val]   # train, val


def link_many(files: list[Path], dest_dir: Path) -> int:
    dest_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in files:
        link = dest_dir / src.name
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(src.resolve(), link)
        n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ml = "/mnt/c/Users/POTATO/Desktop/TomatoCare/ml"
    ap.add_argument("--tomato", default=f"{ml}/dataset/raw/tomato20k")
    ap.add_argument("--plantvillage", default=f"{ml}/dataset/raw/plantvillage/PlantVillage")
    ap.add_argument("--notleaf", default=str(Path.home() / "tc_data/raw/notleaf"))
    ap.add_argument("--dest", default=str(Path.home() / "tc_data"))
    ap.add_argument("--val-frac", type=float, default=0.15)
    args = ap.parse_args()

    rng = random.Random(SEED)
    dest = Path(args.dest)
    canon = dest / "_img"
    report: dict = {"stages": {}}

    print("=" * 60)
    print("  STEP 1 — canonical copy to ext4 (slow first run)")
    print("=" * 60)

    # --- tomato: copy train + valid, remap class names -----------------
    tomato_train: dict[str, list[Path]] = {}
    tomato_test: dict[str, list[Path]] = {}
    for src_name, key in TOMATO_CLASS_MAP.items():
        tr = list_images(Path(args.tomato) / "train" / src_name)
        te = list_images(Path(args.tomato) / "valid" / src_name)
        tomato_train[key] = copy_into(tr, canon / "tomato" / "train" / key)
        tomato_test[key] = copy_into(te, canon / "tomato" / "valid" / key)
        print(f"  tomato/{key:<22} train={len(tr):<5} test={len(te)}")

    # --- other_leaf: PlantVillage non-tomato (potato + pepper) ---------
    other_leaf: list[Path] = []
    for cls_dir in sorted(Path(args.plantvillage).iterdir()):
        if cls_dir.is_dir() and not cls_dir.name.startswith("Tomato"):
            imgs = list_images(cls_dir)
            other_leaf += copy_into(imgs, canon / "other_leaf" / cls_dir.name)
            print(f"  other_leaf/{cls_dir.name:<32} {len(imgs)}")

    # --- not_leaf: imagenette (already on ext4) ------------------------
    not_leaf = [p for p in Path(args.notleaf).rglob("*.jpg")]
    print(f"  not_leaf (imagenette)                       {len(not_leaf)}")

    print("\n" + "=" * 60)
    print("  STEP 2 — split + symlink farm")
    print("=" * 60)

    farm = dest  # stages live directly under dest

    # ---- Stage 3: disease (train/val from tomato train; test from valid)
    s3 = farm / "stage3_disease"
    if s3.exists():
        shutil.rmtree(s3)
    s3_counts = {"train": {}, "val": {}, "test": {}}
    tomato_train_split: dict[str, tuple[list[Path], list[Path]]] = {}
    for key, files in tomato_train.items():
        tr, va = split_train_val(files, args.val_frac, rng)
        tomato_train_split[key] = (tr, va)
        s3_counts["train"][key] = link_many(tr, s3 / "train" / key)
        s3_counts["val"][key] = link_many(va, s3 / "val" / key)
        s3_counts["test"][key] = link_many(tomato_test[key], s3 / "test" / key)
    report["stages"]["stage3_disease"] = s3_counts

    # ---- Stage 2: tomato gate (tomato vs other_leaf) ------------------
    s2 = farm / "stage2_tomato"
    if s2.exists():
        shutil.rmtree(s2)
    tomato_tr_all = [p for (tr, _) in tomato_train_split.values() for p in tr]
    tomato_va_all = [p for (_, va) in tomato_train_split.values() for p in va]
    ol_tr, ol_va = split_train_val(other_leaf, args.val_frac, rng)
    s2_counts = {
        "train": {
            "tomato": link_many(tomato_tr_all, s2 / "train" / "tomato"),
            "other_leaf": link_many(ol_tr, s2 / "train" / "other_leaf"),
        },
        "val": {
            "tomato": link_many(tomato_va_all, s2 / "val" / "tomato"),
            "other_leaf": link_many(ol_va, s2 / "val" / "other_leaf"),
        },
    }
    report["stages"]["stage2_tomato"] = s2_counts

    # ---- Stage 1: leaf gate (leaf vs not_leaf) ------------------------
    s1 = farm / "stage1_leaf"
    if s1.exists():
        shutil.rmtree(s1)
    nl_tr, nl_va = split_train_val(not_leaf, args.val_frac, rng)
    s1_counts = {
        "train": {
            "leaf": link_many(tomato_tr_all + ol_tr, s1 / "train" / "leaf"),
            "not_leaf": link_many(nl_tr, s1 / "train" / "not_leaf"),
        },
        "val": {
            "leaf": link_many(tomato_va_all + ol_va, s1 / "val" / "leaf"),
            "not_leaf": link_many(nl_va, s1 / "val" / "not_leaf"),
        },
    }
    report["stages"]["stage1_leaf"] = s1_counts

    (dest / "dataset_report.json").write_text(json.dumps(report, indent=2))
    print("\n--- summary ---")
    for stage, splits in report["stages"].items():
        print(f"{stage}:")
        for split, classes in splits.items():
            total = sum(classes.values())
            print(f"  {split:<6} total={total:<7} {classes}")
    print(f"\n[done] staged dataset at {dest}")


if __name__ == "__main__":
    main()
