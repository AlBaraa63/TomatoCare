"""A2 — Dataset inventory + stratified split.

Two operating modes, selected automatically based on training_config.yaml:

  Mode A — Pre-split (preferred when pre_split_root is set):
    Reads an existing <pre_split_root>/{train,val,test}/<folder>/*.{jpg,png}
    layout directly and writes CSVs without stratified resampling. Used to
    consume the cleaned, deduplicated dataset inherited from the previous
    TomatoCare attempt (32,653 images, 91.17% PyTorch baseline). The
    class_aliases map translates source folder names ("Bacterial_spot") to
    canonical class names ("Tomato_Bacterial_spot") so class_index stays
    consistent with the canonical classes list.

  Mode B — Multi-root stratified split (fallback):
    Walks every dataset_root, merges per-class lists, and performs a
    70/15/15 stratified split with random_state=42.

In both modes, the script verifies all 10 required classes are present in
the relevant splits and fails fast otherwise. Caching: re-running with all
three CSVs and the dataset_report present skips work entirely.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# Make sibling utils importable when invoked as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402


# Image extensions PlantVillage / Mendeley / multi-source ship with.
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def resolve_cross_platform_path(raw: str, project_root_dir: Path) -> Path | None:
    """Resolve a config path that may have been written on a different OS.

    The same training_config.yaml is used from Windows (during code editing)
    and from WSL (during training). pre_split_root in particular tends to be
    a Windows absolute path; under WSL the same data lives at /mnt/c/...
    This helper tries the path as-is first, then translates Windows<->WSL.
    Returns the first variant that exists as a directory, or None.
    """
    candidates: list[Path] = []

    # 1. As written.
    candidates.append(Path(raw))

    # 2. Relative-to-project resolution (for paths like "dataset/raw/x").
    if not Path(raw).is_absolute():
        candidates.append(project_root_dir / raw)

    # 3. Windows path used from a Linux/WSL shell: C:\... -> /mnt/c/...
    if sys.platform != "win32" and len(raw) >= 2 and raw[1] == ":":
        drive = raw[0].lower()
        rest = raw[2:].replace("\\", "/").lstrip("/")
        candidates.append(Path(f"/mnt/{drive}/{rest}"))

    # 4. WSL mount path used from Windows: /mnt/c/... -> C:\...
    if sys.platform == "win32" and raw.startswith("/mnt/") and len(raw) > 7:
        drive = raw[5].upper()
        rest = raw[6:].lstrip("/")
        candidates.append(Path(f"{drive}:/{rest}"))

    for c in candidates:
        if c.is_dir():
            return c
    return None


def banner_script(purpose: str) -> None:
    print("##############################################################")
    print(f"  TomatoCare — {purpose}")
    print(f"  Device : cpu  (inventory does not require GPU)")
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


def inventory_pre_split(pre_split_root: Path, classes: list[str],
                        aliases: dict[str, str]) -> dict[str, list[tuple[Path, str, int]]]:
    """Walk <pre_split_root>/{train,val,test}/<source_folder>/*.{jpg,png}.

    Each row returned is (absolute_filepath, canonical_class_name, class_index).
    Source folder names are remapped through `aliases`. If a source folder
    has no entry in `aliases` and is not already a canonical class, it is
    skipped with a warning — this catches typos and unexpected folders
    without silently mis-labelling images.
    """
    canonical_set = set(classes)
    canonical_index = {c: i for i, c in enumerate(classes)}
    splits: dict[str, list[tuple[Path, str, int]]] = {
        "train": [], "val": [], "test": []
    }

    for split in splits:
        sd = pre_split_root / split
        if not sd.is_dir():
            raise FileNotFoundError(
                f"Pre-split data missing the '{split}' folder at {sd}. "
                "Expected layout: <pre_split_root>/{train,val,test}/<class>/"
            )
        for cls_dir in sorted(sd.iterdir()):
            if not cls_dir.is_dir():
                continue
            source_name = cls_dir.name
            # Resolve source folder → canonical class via aliases, falling
            # back to identity if the folder already matches a canonical name.
            canonical = aliases.get(source_name, source_name)
            if canonical not in canonical_set:
                print(f"  >> SKIP unknown folder: {sd.name}/{source_name} "
                      f"(no alias to a canonical class)")
                continue
            idx = canonical_index[canonical]
            files = [p for p in cls_dir.iterdir()
                     if p.is_file() and p.suffix in IMAGE_EXTS]
            for p in files:
                splits[split].append((p, canonical, idx))
    return splits


def inventory_root(root: Path, classes: list[str]) -> dict[str, list[Path]]:
    """Return {class_name: [image_paths]} for one dataset root.

    Missing class folders are returned as empty lists — A2 fails only after
    merging all roots if any class is still empty.
    """
    out: dict[str, list[Path]] = {c: [] for c in classes}
    if not root.exists():
        print(f"  >> SKIP root (not present): {root}")
        return out
    for cls in classes:
        cls_dir = root / cls
        if not cls_dir.exists():
            continue
        files = [p for p in cls_dir.iterdir()
                 if p.is_file() and p.suffix in IMAGE_EXTS]
        out[cls] = files
    return out


def merge_inventories(parts: list[dict[str, list[Path]]],
                      classes: list[str]) -> dict[str, list[Path]]:
    merged: dict[str, list[Path]] = {c: [] for c in classes}
    for part in parts:
        for cls in classes:
            merged[cls].extend(part[cls])
    return merged


def main() -> None:
    banner_script("A2 Dataset Inventory + Stratified Split")
    set_seed(42)

    config = load_config()
    classes: list[str] = config["classes"]
    root = project_root()
    splits_dir = root / config["paths"]["splits_dir"]
    results_dir = root / config["paths"]["results_dir"]
    splits_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Cache check — skip entirely if all artifacts exist.
    train_csv = splits_dir / "train.csv"
    val_csv = splits_dir / "val.csv"
    test_csv = splits_dir / "test.csv"
    report_path = results_dir / "dataset_report.json"
    if train_csv.exists() and val_csv.exists() and test_csv.exists() \
            and report_path.exists():
        print(f"  >> SKIP: splits already exist at {splits_dir}. "
              "Delete to re-run.")
        with open(report_path, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
        return

    # ----- Mode A: pre-split data (preferred) ----------------------------
    pre_split_cfg = config.get("pre_split_root")
    if pre_split_cfg:
        pre_split_root = resolve_cross_platform_path(pre_split_cfg, root)
        if pre_split_root is not None:
            print(f"  >> Resolved pre_split_root: {pre_split_root}")
            banner_phase("Pre-Split Inventory")
            aliases = config.get("class_aliases", {}) or {}
            splits = inventory_pre_split(pre_split_root, classes, aliases)

            # Verify every canonical class has at least one image per split.
            missing: list[str] = []
            for split_name, rows in splits.items():
                seen = {r[1] for r in rows}
                for cls in classes:
                    if cls not in seen:
                        missing.append(f"{split_name}/{cls}")
            for cls in classes:
                idx = classes.index(cls)
                per_split = {sp: sum(1 for r in splits[sp] if r[1] == cls)
                             for sp in ("train", "val", "test")}
                banner_step(f"INV-{idx:02d}", cls, **per_split)
            if missing:
                raise FileNotFoundError(
                    "Pre-split data missing canonical classes in some splits: "
                    f"{missing}. Check class_aliases in training_config.yaml."
                )

            for split_name, rows in splits.items():
                out = splits_dir / f"{split_name}.csv"
                pd.DataFrame(
                    [{"filepath": str(p), "label": c, "class_index": i}
                     for (p, c, i) in rows]
                ).to_csv(out, index=False)
            banner_step(
                "SPL-PRE", "Pre-split CSVs written",
                train=len(splits["train"]),
                val=len(splits["val"]),
                test=len(splits["test"]),
            )
            print(f"  >> Saved to : {splits_dir}")

            report = {
                "mode": "pre_split",
                "pre_split_root": str(pre_split_root),
                "total_images": sum(len(rs) for rs in splits.values()),
                "classes": classes,
                "class_aliases": aliases,
                "per_class_per_split": {
                    cls: {
                        sp: sum(1 for r in splits[sp] if r[1] == cls)
                        for sp in ("train", "val", "test")
                    }
                    for cls in classes
                },
                "splits": {sp: len(rs) for sp, rs in splits.items()},
            }
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            banner_step("RPT-01", "Dataset report saved",
                        path=str(report_path))
            return
        else:
            print(f"  >> pre_split_root configured but no variant resolved: "
                  f"{pre_split_cfg}")
            print(f"  >> (tried as-is, project-relative, "
                  f"Windows↔WSL translation)")
            print(f"  >> Falling back to multi-root stratified split.")

    # ----- Mode B: multi-root stratified split (fallback) ----------------
    banner_phase("Dataset Inventory")
    dataset_roots = [root / r for r in config["dataset_roots"]]
    parts = [inventory_root(r, classes) for r in dataset_roots]
    merged = merge_inventories(parts, classes)

    missing = [c for c, files in merged.items() if not files]
    for cls in classes:
        n = len(merged[cls])
        banner_step(f"INV-{classes.index(cls):02d}", cls, images=n)
    if missing:
        raise FileNotFoundError(
            "Required classes have zero images across all dataset roots: "
            f"{missing}. Check that the folder names under your dataset_roots "
            "match the 'classes' list in training_config.yaml exactly."
        )

    # Build a flat (filepath, label, class_index) frame.
    rows = []
    for idx, cls in enumerate(classes):
        for p in merged[cls]:
            rows.append({"filepath": str(p), "label": cls, "class_index": idx})
    df = pd.DataFrame(rows)
    print(f"  >> Total images : {len(df)}")
    print(f"  >> Classes      : {len(classes)}")

    banner_phase("Stratified Split")
    tr_ratio = config["train_ratio"]
    va_ratio = config["val_ratio"]
    te_ratio = config["test_ratio"]
    assert abs(tr_ratio + va_ratio + te_ratio - 1.0) < 1e-6, \
        "train+val+test ratios must sum to 1.0"

    # Two-step split: first carve off test, then split remainder into train/val.
    rest, test = train_test_split(
        df, test_size=te_ratio, random_state=42,
        stratify=df["class_index"])
    val_size_of_rest = va_ratio / (tr_ratio + va_ratio)
    train, val = train_test_split(
        rest, test_size=val_size_of_rest, random_state=42,
        stratify=rest["class_index"])

    train.to_csv(train_csv, index=False)
    val.to_csv(val_csv, index=False)
    test.to_csv(test_csv, index=False)
    banner_step("SPL-01", "Stratified split written",
                train=len(train), val=len(val), test=len(test))
    print(f"  >> Saved to : {splits_dir}")

    # Report.
    report = {
        "total_images": int(len(df)),
        "classes": classes,
        "per_class_total": {
            cls: int((df["label"] == cls).sum()) for cls in classes
        },
        "splits": {
            "train": int(len(train)),
            "val": int(len(val)),
            "test": int(len(test)),
        },
        "split_ratios": {
            "train": tr_ratio, "val": va_ratio, "test": te_ratio
        },
        "dataset_roots_used": [
            str(r) for r in dataset_roots if r.exists()
        ],
        "random_state": 42,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Dataset report saved", path=str(report_path))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(f"\n[FATAL] {exc}")
        print(
            "\nDownload instructions:\n"
            "  Kaggle (PlantVillage):\n"
            "    kaggle datasets download arjuntejaswi/plant-village -p ml/dataset/raw/\n"
            "    unzip and move the 10 Tomato_* folders into ml/dataset/raw/plantvillage/\n"
            "  Kaggle (multi-source):\n"
            "    kaggle datasets download cookiefinder/tomato-disease-multiple-sources -p ml/dataset/raw/\n"
            "  Mendeley DOI 10.17632/tywbtsjrjv.1:\n"
            "    Download manually from https://data.mendeley.com/datasets/tywbtsjrjv/1\n"
            "    Extract Tomato* folders into ml/dataset/raw/mendeley/\n"
        )
        sys.exit(1)
