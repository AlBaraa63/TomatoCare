"""A7 — Evaluation on the held-out test set.

Loads stage2_best.keras, runs inference on test.csv, computes:
  - overall accuracy
  - per-class precision / recall / F1
  - macro-averaged F1
  - 10x10 confusion matrix

Saves:
  - ml/results/eval_report.json
  - ml/results/confusion_matrix.png

Pass/fail gate: if overall_accuracy < target_accuracy (0.90), the script
prints a clear error and exits with code 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display needed; we save PNG only
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (classification_report, confusion_matrix,
                             f1_score)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402


def banner_script(purpose: str, device: str) -> None:
    print("##############################################################")
    print(f"  TomatoCare — {purpose}")
    print(f"  Device : {device}")
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


def main() -> None:
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    banner_script("A7 Evaluation", device)

    config = load_config()
    classes: list[str] = config["classes"]
    root = project_root()
    ckpt_path = root / config["paths"]["checkpoints_dir"] / "stage2_best.keras"
    results_dir = root / config["paths"]["results_dir"]
    report_path = results_dir / "eval_report.json"
    cm_path = results_dir / "confusion_matrix.png"

    if not ckpt_path.exists():
        raise FileNotFoundError(
            f"{ckpt_path} not found. Run train_stage2.py first."
        )

    banner_phase("Loading Model + Test Set")
    model = tf.keras.models.load_model(ckpt_path)
    test_csv = root / config["paths"]["splits_dir"] / "test.csv"
    test_ds = build_split_dataset(test_csv, config)
    df = pd.read_csv(test_csv)
    banner_step("LD-01", "Loaded",
                model=str(ckpt_path), test_samples=len(df))

    banner_phase("Running Inference")
    y_true: list[int] = []
    y_pred: list[int] = []
    for batch_x, batch_y in test_ds:
        probs = model.predict(batch_x, verbose=0)
        y_pred.extend(np.argmax(probs, axis=1).tolist())
        y_true.extend(np.argmax(batch_y.numpy(), axis=1).tolist())
    y_true_np = np.array(y_true)
    y_pred_np = np.array(y_pred)

    banner_phase("Computing Metrics")
    overall_acc = float((y_true_np == y_pred_np).mean())
    macro_f1 = float(f1_score(y_true_np, y_pred_np, average="macro",
                              zero_division=0))
    cls_report = classification_report(
        y_true_np, y_pred_np,
        labels=list(range(len(classes))),
        target_names=classes,
        output_dict=True,
        zero_division=0,
    )
    # Reduce to a stable per-class subdict.
    per_class = {
        cls: {
            "precision": float(cls_report[cls]["precision"]),
            "recall": float(cls_report[cls]["recall"]),
            "f1": float(cls_report[cls]["f1-score"]),
            "support": int(cls_report[cls]["support"]),
        }
        for cls in classes
    }
    cm = confusion_matrix(y_true_np, y_pred_np,
                          labels=list(range(len(classes))))

    banner_phase("Evaluation Results")
    banner_step("M-01", "Overall accuracy",
                accuracy=f"{overall_acc*100:.2f}%")
    banner_step("M-02", "Macro-averaged F1",
                macro_f1=f"{macro_f1:.4f}")
    for cls in classes:
        m = per_class[cls]
        banner_step(
            f"PC-{classes.index(cls):02d}", cls,
            precision=f"{m['precision']:.3f}",
            recall=f"{m['recall']:.3f}",
            f1=f"{m['f1']:.3f}",
            support=m["support"],
        )

    # Confusion matrix heatmap.
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=classes, yticklabels=classes, cbar=True,
    )
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(f"TomatoCare — Confusion Matrix (acc={overall_acc*100:.2f}%)")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(cm_path, dpi=120)
    plt.close()
    banner_step("CM-01", "Confusion matrix saved", path=str(cm_path))

    report = {
        "overall_accuracy": overall_acc,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "class_names": classes,
        "test_samples": int(len(df)),
        "model_checkpoint": str(ckpt_path),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Eval report saved", path=str(report_path))

    target = config["target_accuracy"]
    if overall_acc < target:
        print(f"\n[FAIL] TARGET NOT MET: accuracy={overall_acc:.4f} "
              f"< {target} required.")
        print("       Check augmentation quality, class balance, and retrain.")
        sys.exit(1)
    else:
        print(f"\n[PASS] Accuracy {overall_acc:.4f} >= target {target}.")


if __name__ == "__main__":
    main()
