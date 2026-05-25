"""TREE / evaluate — per-stage metrics + end-to-end cascade + rejection rates.

This is the script that answers the question v1 failed: *does the tree reject
things that are not a tomato leaf, instead of confidently mislabelling them?*

It reports four things:
  1. Stage 3 disease accuracy on the held-out tomato TEST split (honest — these
     images were never trained on; the split came from tomato20k/valid).
  2. Stage 1 leaf-gate accuracy + not-leaf rejection recall (on its val split).
  3. Stage 2 tomato-gate accuracy + other-leaf rejection recall (on its val split).
  4. END-TO-END cascade on the tomato test set: what fraction survive both gates
     and get the correct diagnosis — the number that actually matters to a user.

Note: gate negatives (other_leaf, not_leaf) are scored on their val splits,
which influenced early stopping, so those numbers are mildly optimistic. A
dedicated hard-negative test set (unseen species + real non-leaf photos) is
flagged as follow-up.

Run inside the WSL venv (after training all three stages):
    python ml/tree/evaluate_tree.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import tensorflow as tf

IMG = 224
AUTOTUNE = tf.data.AUTOTUNE
DATA = Path.home() / "tc_data"
MODELS = DATA / "models"


def load_meta(stage: str) -> list[str]:
    meta = json.loads((MODELS / f"{stage}.meta.json").read_text())
    return meta["class_names"]


def eval_dir(model, directory: Path):
    """Return (y_true, y_pred, probs) over a labelled directory, no shuffle."""
    ds = tf.keras.utils.image_dataset_from_directory(
        directory, labels="inferred", label_mode="int",
        image_size=(IMG, IMG), crop_to_aspect_ratio=True,
        batch_size=64, shuffle=False)
    class_names = ds.class_names
    ds = ds.map(lambda x, y: (tf.cast(x, tf.float32) / 255.0, y),
                num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
    y_true = np.concatenate([y.numpy() for _, y in ds])
    probs = model.predict(ds, verbose=0)
    return y_true, probs.argmax(1), probs, class_names


def predict_dir(model, directory: Path):
    """Just probs over every image in a directory tree (single implied class)."""
    ds = tf.keras.utils.image_dataset_from_directory(
        directory, labels=None, image_size=(IMG, IMG),
        crop_to_aspect_ratio=True, batch_size=64, shuffle=False)
    ds = ds.map(lambda x: tf.cast(x, tf.float32) / 255.0,
                num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
    return model.predict(ds, verbose=0)


def save_confusion_png(cm: np.ndarray, names: list[str], path: Path) -> None:
    """Row-normalised confusion heatmap for the report. PNG is optional —
    the matrix is always written to eval_report.json regardless."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("[eval] matplotlib unavailable — confusion matrix is in JSON only")
        return
    cmn = cm.astype(float) / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Stage 3 disease - row-normalised confusion")
    for i in range(len(names)):
        for j in range(len(names)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        fontsize=6, color="black" if cmn[i, j] < 0.5 else "white")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"[eval] confusion matrix PNG saved -> {path}")


def main() -> None:
    report: dict = {}
    leaf = tf.keras.models.load_model(MODELS / "stage1_leaf.keras")
    tom = tf.keras.models.load_model(MODELS / "stage2_tomato.keras")
    dis = tf.keras.models.load_model(MODELS / "stage3_disease.keras")

    leaf_names = load_meta("stage1_leaf")      # e.g. ["leaf","not_leaf"]
    tom_names = load_meta("stage2_tomato")     # e.g. ["other_leaf","tomato"]
    dis_names = load_meta("stage3_disease")    # 11 classes
    LEAF = leaf_names.index("leaf")
    NOT_LEAF = leaf_names.index("not_leaf")
    TOMATO = tom_names.index("tomato")
    OTHER = tom_names.index("other_leaf")

    # ---- 1. Stage 3 disease accuracy on held-out tomato TEST ----
    yt, yp, _, names = eval_dir(dis, DATA / "stage3_disease" / "test")
    acc3 = float((yt == yp).mean())
    per_class = {names[i]: round(float(((yt == i) & (yp == i)).sum() /
                                       max((yt == i).sum(), 1)), 4)
                 for i in range(len(names))}
    report["stage3_disease"] = {"test_accuracy": round(acc3, 4),
                                "per_class_recall": per_class,
                                "n_test": int(len(yt))}

    # Confusion matrix for the disease classes (Dr. Yazeed's suggestion for the
    # final report's error analysis). Always in JSON; PNG if matplotlib exists.
    ncls = len(names)
    cm = np.zeros((ncls, ncls), dtype=int)
    for t, p in zip(yt, yp):
        cm[int(t), int(p)] += 1
    report["stage3_disease"]["confusion_matrix"] = {
        "labels": names, "matrix": cm.tolist()}
    save_confusion_png(cm, names, DATA / "confusion_matrix.png")

    # ---- 2. Stage 1 leaf gate ----
    yt1, yp1, _, _ = eval_dir(leaf, DATA / "stage1_leaf" / "val")
    acc1 = float((yt1 == yp1).mean())
    notleaf_recall = float(((yt1 == NOT_LEAF) & (yp1 == NOT_LEAF)).sum() /
                           max((yt1 == NOT_LEAF).sum(), 1))
    report["stage1_leaf"] = {"val_accuracy": round(acc1, 4),
                             "not_leaf_rejection_recall": round(notleaf_recall, 4)}

    # ---- 3. Stage 2 tomato gate ----
    yt2, yp2, _, _ = eval_dir(tom, DATA / "stage2_tomato" / "val")
    acc2 = float((yt2 == yp2).mean())
    other_recall = float(((yt2 == OTHER) & (yp2 == OTHER)).sum() /
                         max((yt2 == OTHER).sum(), 1))
    report["stage2_tomato"] = {"val_accuracy": round(acc2, 4),
                               "other_leaf_rejection_recall": round(other_recall, 4)}

    # ---- 4. END-TO-END cascade on tomato test ----
    test_root = DATA / "stage3_disease" / "test"
    n_total = n_pass_leaf = n_pass_tom = n_correct = 0
    for ci, cname in enumerate(dis_names):
        cdir = test_root / cname
        if not cdir.is_dir() or not any(cdir.iterdir()):
            continue
        p_leaf = predict_dir(leaf, cdir)
        is_leaf = p_leaf.argmax(1) == LEAF
        p_tom = predict_dir(tom, cdir)
        is_tom = p_tom.argmax(1) == TOMATO
        p_dis = predict_dir(dis, cdir)
        dis_pred = p_dis.argmax(1)
        passed = is_leaf & is_tom
        correct = passed & (dis_pred == ci)
        n_total += len(is_leaf)
        n_pass_leaf += int(is_leaf.sum())
        n_pass_tom += int((is_leaf & is_tom).sum())
        n_correct += int(correct.sum())
    report["end_to_end"] = {
        "n_tomato_test": n_total,
        "passed_leaf_gate_pct": round(100 * n_pass_leaf / max(n_total, 1), 2),
        "passed_both_gates_pct": round(100 * n_pass_tom / max(n_total, 1), 2),
        "correct_diagnosis_pct": round(100 * n_correct / max(n_total, 1), 2),
    }

    (DATA / "eval_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
