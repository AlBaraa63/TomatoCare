"""TREE / data — fold MobileSAM background-suppressed images into TRAIN splits.

After segment_leaves.py writes ~/tc_data/_seg/<stage>/<class>/seg_*.jpg, this
symlinks them into the matching train folders so the classifier trains on a
RAW + BACKGROUND-SUPPRESSED mix. The model then can't lean on background, which
is the lab->field / UAE robustness win — while the raw copies keep it from
over-fitting to the (imperfect) masks.

Additive + idempotent (skips links that already exist). val/test are left
untouched, so evaluation stays honest and comparable to the previous run.

Run inside the WSL venv, then retrain stage2 + stage3:
    python ml/tree/fold_suppressed.py
"""
from __future__ import annotations

import os
from pathlib import Path

SEG = Path.home() / "tc_data" / "_seg"
FARMS = {"stage2": "stage2_tomato", "stage3": "stage3_disease"}


def main() -> None:
    for seg_key, farm in FARMS.items():
        src_root = SEG / seg_key
        dst_root = Path.home() / "tc_data" / farm / "train"
        if not src_root.is_dir():
            print(f"[skip] {src_root} missing")
            continue
        linked = skipped = 0
        for cls_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
            dst = dst_root / cls_dir.name
            dst.mkdir(parents=True, exist_ok=True)
            for img in cls_dir.iterdir():
                if not img.is_file():
                    continue
                link = dst / img.name           # already 'seg_'-prefixed, unique
                if link.exists() or link.is_symlink():
                    skipped += 1
                    continue
                os.symlink(img.resolve(), link)
                linked += 1
        print(f"{farm}: linked {linked} suppressed images into train "
              f"({skipped} already present)")

    print("\n[done] suppressed images folded in. Retrain stage2 + stage3.")


if __name__ == "__main__":
    main()
