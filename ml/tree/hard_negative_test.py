"""TREE / evaluate — HONEST hard-negative test on data the gates never saw.

evaluate_tree.py scored the gates on their own val splits (used for early
stopping -> mildly optimistic). This script is the real exam:

  * UNSEEN SPECIES  — PlantVillage crops the tomato gate never trained on
    (apple, corn, grape, cherry, ...). These ARE leaves, so the leaf gate
    should pass them, and the TOMATO gate should REJECT them as 'other_leaf'.
    The failure we care about: an unseen leaf sailing through BOTH gates and
    getting a bogus tomato diagnosis (exactly v1's bug).

  * REAL NON-LEAF   — natural-images (people, cars, animals, ...), a different
    source than the imagenette the leaf gate trained on. The LEAF gate should
    reject these as 'not_leaf'.

Robust to corrupt files: each image is decoded with the same tf op training
uses, wrapped in ignore_errors() so a bad file is skipped, not fatal.

Run inside the WSL venv (after training):
    python ml/tree/hard_negative_test.py \
        --species-root /mnt/c/.../plantvillage_full/<...>/color \
        --nonleaf-root /mnt/c/.../natural_images/<...>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

IMG = 224
AUTOTUNE = tf.data.AUTOTUNE
MODELS = Path.home() / "tc_data" / "models"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def load_meta(stage: str) -> list[str]:
    return json.loads((MODELS / f"{stage}.meta.json").read_text())["class_names"]


def files_under(d: Path) -> list[str]:
    return [str(p) for p in d.rglob("*") if p.suffix.lower() in IMG_EXTS]


def _decode(path):
    raw = tf.io.read_file(path)
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    img = tf.image.resize(img, [IMG, IMG])
    img = tf.cast(img, tf.float32) / 255.0
    img.set_shape([IMG, IMG, 3])
    return img


def predict_files(model, files: list[str]) -> np.ndarray:
    ds = (tf.data.Dataset.from_tensor_slices(files)
          .map(_decode, num_parallel_calls=AUTOTUNE)
          .apply(tf.data.experimental.ignore_errors())
          .batch(64).prefetch(AUTOTUNE))
    return model.predict(ds, verbose=0)


def subdirs_with_images(root: Path, exclude: list[str]) -> list[Path]:
    out = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        low = d.name.lower()
        if any(x in low for x in exclude):
            continue
        if files_under(d):
            out.append(d)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--species-root", required=True)
    ap.add_argument("--nonleaf-root", required=True)
    ap.add_argument("--species-exclude", default="tomato,potato,pepper")
    ap.add_argument("--nonleaf-exclude", default="flower,fruit")
    ap.add_argument("--out", default=str(Path.home() / "tc_data" / "hard_negative_report.json"))
    args = ap.parse_args()

    leaf = tf.keras.models.load_model(MODELS / "stage1_leaf.keras")
    tom = tf.keras.models.load_model(MODELS / "stage2_tomato.keras")
    ln, tn = load_meta("stage1_leaf"), load_meta("stage2_tomato")
    LEAF, NOT_LEAF = ln.index("leaf"), ln.index("not_leaf")
    TOMATO, OTHER = tn.index("tomato"), tn.index("other_leaf")

    report: dict = {"unseen_species": {"per_species": {}}, "real_non_leaf": {"per_class": {}}}

    # ---- UNSEEN SPECIES: tomato gate should reject (other_leaf) ----
    sp_excl = [s.strip().lower() for s in args.species_exclude.split(",")]
    tot = leaked = leaf_pass = tom_reject = 0
    for d in subdirs_with_images(Path(args.species_root), sp_excl):
        files = files_under(d)
        is_leaf = predict_files(leaf, files).argmax(1) == LEAF
        is_tom = predict_files(tom, files).argmax(1) == TOMATO
        n = min(len(is_leaf), len(is_tom))
        is_leaf, is_tom = is_leaf[:n], is_tom[:n]
        passed_both = int((is_leaf & is_tom).sum())
        report["unseen_species"]["per_species"][d.name] = {
            "n": int(n),
            "tomato_gate_reject_pct": round(100 * float((~is_tom).mean()), 2),
            "leaked_to_diagnosis_pct": round(100 * passed_both / max(n, 1), 2),
        }
        tot += n; leaked += passed_both
        leaf_pass += int(is_leaf.sum()); tom_reject += int((~is_tom).sum())
    report["unseen_species"]["overall"] = {
        "n": int(tot),
        "leaf_gate_pass_pct": round(100 * leaf_pass / max(tot, 1), 2),
        "tomato_gate_reject_pct": round(100 * tom_reject / max(tot, 1), 2),
        "leaked_to_diagnosis_pct": round(100 * leaked / max(tot, 1), 2),
    }

    # ---- REAL NON-LEAF: leaf gate should reject (not_leaf) ----
    nl_excl = [s.strip().lower() for s in args.nonleaf_exclude.split(",")]
    tot = leaked = nl_reject = 0
    for d in subdirs_with_images(Path(args.nonleaf_root), nl_excl):
        files = files_under(d)
        is_leaf = predict_files(leaf, files).argmax(1) == LEAF
        is_tom = predict_files(tom, files).argmax(1) == TOMATO
        n = min(len(is_leaf), len(is_tom))
        is_leaf, is_tom = is_leaf[:n], is_tom[:n]
        passed_both = int((is_leaf & is_tom).sum())
        report["real_non_leaf"]["per_class"][d.name] = {
            "n": int(n),
            "leaf_gate_reject_pct": round(100 * float((~is_leaf).mean()), 2),
            "leaked_to_diagnosis_pct": round(100 * passed_both / max(n, 1), 2),
        }
        tot += n; leaked += passed_both
        nl_reject += int((~is_leaf).sum())
    report["real_non_leaf"]["overall"] = {
        "n": int(tot),
        "leaf_gate_reject_pct": round(100 * nl_reject / max(tot, 1), 2),
        "leaked_to_diagnosis_pct": round(100 * leaked / max(tot, 1), 2),
    }

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
