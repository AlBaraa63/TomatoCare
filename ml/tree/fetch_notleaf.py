"""TREE / data — fetch the 'not-leaf' negatives for the Stage-1 leaf gate.

The leaf gate answers a single question: *is there a leaf in this photo at all?*
Its negative class therefore needs images that are clearly NOT leaves — random
everyday objects, animals, people, vehicles, scenes. We use `imagenette`
(a 10-class ImageNet subset: fish, dog, cassette player, chainsaw, church,
French horn, garbage truck, gas pump, golf ball, parachute) shipped via
tensorflow_datasets. It's permissively licensed, ~340 MB, and downloads fast.

Output (materialised as plain JPEGs so the rest of the pipeline can treat it
like any image folder):

    <out_dir>/<wnid>/<idx>.jpg

We write to the Linux ext4 filesystem by default (NOT /mnt/c) because training
reads these every epoch and 9P/NTFS reads would starve the GPU.

Usage (inside WSL venv):
    python ml/tree/fetch_notleaf.py
    python ml/tree/fetch_notleaf.py --out /home/albaraa/tc_data/raw/notleaf --limit 13000
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(Path.home() / "tc_data" / "raw" / "notleaf"),
        help="Destination directory for materialised not-leaf JPEGs (ext4).",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional cap on number of images (0 = all of imagenette, ~13k).",
    )
    args = ap.parse_args()

    out_dir = Path(args.out)
    sentinel = out_dir / ".materialised"
    if sentinel.exists():
        existing = sum(1 for _ in out_dir.rglob("*.jpg"))
        print(f"[skip] already materialised: {existing} images at {out_dir}")
        return

    # Heavy imports kept inside main so --help is instant.
    import numpy as np
    import tensorflow_datasets as tfds
    from PIL import Image
    from tqdm import tqdm

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[dl] downloading imagenette/320px-v2 via tensorflow_datasets ...")
    ds_train, ds_val = tfds.load(
        "imagenette/320px-v2",
        split=["train", "validation"],
        as_supervised=False,
        shuffle_files=False,
    )
    label_names = tfds.builder("imagenette/320px-v2").info.features["label"].names

    idx = 0
    for ds in (ds_train, ds_val):
        for ex in tqdm(tfds.as_numpy(ds), desc="materialising"):
            if args.limit and idx >= args.limit:
                break
            wnid = label_names[int(ex["label"])]
            d = out_dir / wnid
            d.mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.asarray(ex["image"])).convert("RGB").save(
                d / f"{idx:06d}.jpg", "JPEG", quality=90
            )
            idx += 1

    sentinel.write_text("ok\n", encoding="utf-8")
    print(f"[done] materialised {idx} not-leaf images across "
          f"{len(label_names)} categories -> {out_dir}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"[FATAL] missing dependency: {exc}", file=sys.stderr)
        print("Activate the WSL venv: source ~/.venvs/tomatocare-wsl/bin/activate")
        sys.exit(1)
