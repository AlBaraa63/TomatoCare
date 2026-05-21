"""A2.5 — Prepare OOD negatives (the Tomato_NotALeaf reject class).

Downloads the `imagenette/320px-v2` tensorflow_datasets release (~13k photos
of dogs, fish, cars, etc — i.e. things that are clearly NOT tomato leaves)
and emits a CSV per split:

    ml/dataset/raw/notaleaf/{train,val,test}/<wnid>/<file>.jpeg
    ml/dataset/splits/notaleaf.csv  (columns: filepath, label, class_index, source_wnid)

A2 (prepare_plantvillage.py) appends those rows into train.csv / val.csv /
test.csv after building the tomato split, so the final per-split CSV mixes
10 tomato classes + the reject class.

Why a separate script:
  - The download is large and slow; we want strict caching so re-runs are
    instant.
  - The negatives split is GROUP-AWARE on imagenette's wnid sub-category
    (e.g. n02102040, n03028079) — the same scene type cannot leak between
    train and test. The tomato pipeline doesn't have that concept, so we
    keep the negative-handling logic isolated here.
  - If we ever swap the negative source (Open Images, DTD, etc), only this
    script changes; the rest of the pipeline is source-agnostic.

Caching: if notaleaf.csv exists AND the raw image cache exists, the script
prints counts and exits. Delete one to force a re-run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402


def banner_script(purpose: str) -> None:
    print("##############################################################")
    print(f"  TomatoCare — {purpose}")
    print(f"  Device : cpu  (download only)")
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


def _group_aware_split(items: list[tuple[Path, str]],
                       n_train: int, n_val: int, n_test: int,
                       seed: int) -> dict[str, list[tuple[Path, str]]]:
    """Split images by their group (wnid), not by random sampling.

    Strategy: shuffle the groups (not the images), pick whole groups until
    each split is filled. This guarantees no group appears in two splits.
    If group sizes are uneven, the last group added to a split may push it
    slightly past its target — that's fine, we cap by truncation afterwards.
    """
    import random
    rng = random.Random(seed)

    by_group: dict[str, list[Path]] = {}
    for path, group in items:
        by_group.setdefault(group, []).append(path)

    groups = list(by_group.keys())
    rng.shuffle(groups)
    # Also shuffle within each group for stable but mixed file ordering.
    for g in groups:
        rng.shuffle(by_group[g])

    out: dict[str, list[tuple[Path, str]]] = {"train": [], "val": [], "test": []}
    targets = {"train": n_train, "val": n_val, "test": n_test}

    # Fill train first, then val, then test. Greedy by group.
    for split in ("train", "val", "test"):
        while groups and len(out[split]) < targets[split]:
            g = groups.pop(0)
            for p in by_group[g]:
                out[split].append((p, g))
                if len(out[split]) >= targets[split]:
                    break

    # Truncate to exact target counts (the last-added group may overflow).
    for split in out:
        out[split] = out[split][:targets[split]]

    return out


def _download_imagenette(cache_dir: Path) -> list[tuple[Path, str]]:
    """Materialise imagenette to disk and return (path, wnid) tuples.

    tensorflow_datasets stores its own cached copy; we re-export each image
    as a JPEG into cache_dir/<wnid>/<idx>.jpg so the rest of the pipeline
    can treat it as plain files (same as the tomato data). This costs a few
    minutes once.
    """
    import tensorflow_datasets as tfds
    import tensorflow as tf
    from PIL import Image
    import numpy as np
    from tqdm import tqdm

    cache_dir.mkdir(parents=True, exist_ok=True)
    sentinel = cache_dir / ".materialised"
    if sentinel.exists():
        print(f"  >> Reusing materialised imagenette at {cache_dir}")
        items: list[tuple[Path, str]] = []
        for wnid_dir in sorted(cache_dir.iterdir()):
            if not wnid_dir.is_dir():
                continue
            for p in wnid_dir.iterdir():
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    items.append((p, wnid_dir.name))
        print(f"  >> Found {len(items)} cached negative images")
        return items

    print("  >> Downloading imagenette/320px-v2 via tensorflow_datasets...")
    # We take both 'train' and 'validation' splits — imagenette's split is
    # ImageNet-style 9469 / 3925, but we re-split group-aware below anyway.
    ds_train, ds_val = tfds.load(
        "imagenette/320px-v2",
        split=["train", "validation"],
        as_supervised=False,
        with_info=False,
        shuffle_files=False,
    )

    builder = tfds.builder("imagenette/320px-v2")
    label_names = builder.info.features["label"].names
    # label_names look like 'n01440764', 'n02102040', ... — these ARE wnids.

    items: list[tuple[Path, str]] = []
    idx = 0
    for ds in (ds_train, ds_val):
        for example in tqdm(tfds.as_numpy(ds), desc="materialising"):
            img = example["image"]
            label = int(example["label"])
            wnid = label_names[label]
            wnid_dir = cache_dir / wnid
            wnid_dir.mkdir(parents=True, exist_ok=True)
            out = wnid_dir / f"{idx:06d}.jpg"
            Image.fromarray(np.asarray(img)).convert("RGB").save(
                out, "JPEG", quality=90)
            items.append((out, wnid))
            idx += 1

    sentinel.write_text("ok\n", encoding="utf-8")
    print(f"  >> Materialised {len(items)} images across {len(label_names)} wnids")
    return items


def main() -> None:
    banner_script("A2.5 OOD Negatives Preparation")
    set_seed(42)

    config = load_config()
    root = project_root()
    ood = config.get("ood") or {}
    if not ood:
        print("  >> No 'ood:' section in training_config.yaml; nothing to do.")
        return

    class_name = ood["class_name"]
    if class_name not in config["classes"]:
        raise ValueError(
            f"ood.class_name='{class_name}' is not in config['classes']. "
            "Add it to the classes list first."
        )
    class_index = config["classes"].index(class_name)

    raw_dir = root / config["paths"]["raw_negatives_dir"]
    splits_dir = root / config["paths"]["splits_dir"]
    results_dir = root / config["paths"]["results_dir"]
    splits_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = splits_dir / "notaleaf.csv"
    report_path = results_dir / "negatives_report.json"

    if csv_path.exists() and report_path.exists():
        print(f"  >> SKIP: {csv_path} exists. Delete to re-run.")
        with open(report_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    banner_phase("Download + Materialise Negatives")
    items = _download_imagenette(raw_dir)
    if not items:
        raise RuntimeError(
            "No negative images were materialised. Check that "
            "tensorflow_datasets is installed and the imagenette download "
            "completed. Re-run after fixing."
        )
    banner_step("DL-01", "Negatives materialised",
                source=ood["negative_source"],
                total=len(items),
                wnids=len({g for _, g in items}))

    banner_phase("Group-Aware Split")
    split = _group_aware_split(
        items,
        n_train=ood["target_train_count"],
        n_val=ood["target_val_count"],
        n_test=ood["target_test_count"],
        seed=42,
    )

    rows = []
    for split_name, lst in split.items():
        for path, wnid in lst:
            rows.append({
                "filepath": str(path),
                "label": class_name,
                "class_index": class_index,
                "source_wnid": wnid,
                "split": split_name,
            })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    per_split = {sp: int((df["split"] == sp).sum())
                 for sp in ("train", "val", "test")}
    banner_step("SPL-NEG", "Negatives split written",
                csv=str(csv_path), **per_split)

    # Spot-check no group overlap between splits.
    train_groups = set(df[df["split"] == "train"]["source_wnid"])
    val_groups = set(df[df["split"] == "val"]["source_wnid"])
    test_groups = set(df[df["split"] == "test"]["source_wnid"])
    leakage = (train_groups & val_groups) | (train_groups & test_groups) \
        | (val_groups & test_groups)
    if leakage:
        raise RuntimeError(
            f"Group-aware split failed: wnids appear in multiple splits: "
            f"{sorted(leakage)}. Increase the negative source size or "
            "lower target counts."
        )
    banner_step("CHK-01", "No wnid leakage between splits",
                train_wnids=len(train_groups),
                val_wnids=len(val_groups),
                test_wnids=len(test_groups))

    report = {
        "class_name": class_name,
        "class_index": class_index,
        "negative_source": ood["negative_source"],
        "raw_dir": str(raw_dir),
        "total_materialised": len(items),
        "splits": per_split,
        "wnids_per_split": {
            "train": sorted(train_groups),
            "val": sorted(val_groups),
            "test": sorted(test_groups),
        },
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Negatives report saved", path=str(report_path))

    print()
    print("##############################################################")
    print("  Next step: python -m ml.scripts.prepare_plantvillage")
    print("  (will append notaleaf.csv rows into train/val/test CSVs)")
    print("##############################################################")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        print(f"\n[FATAL] Missing dependency: {exc}")
        print("\nInstall with:\n  pip install -r ml/requirements.txt\n"
              "(needs tensorflow-datasets + tensorflow already installed)")
        sys.exit(1)
