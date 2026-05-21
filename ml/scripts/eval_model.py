"""A7 — Evaluation on the held-out test set (11-class + OOD).

Loads stage2_calibrated.keras (preferred) or stage2_best.keras (fallback)
and runs inference on test.csv. Computes:
  - overall accuracy
  - per-class precision / recall / F1
  - macro-averaged F1
  - 11x11 confusion matrix
  - ECE (Expected Calibration Error) + Brier score
  - OOD-specific metrics: binary leaf-vs-notleaf rejection recall, false-
    reject rate, AUROC, FPR@95%TPR

Saves:
  - ml/results/eval_report.json
  - ml/results/confusion_matrix.png
  - ml/results/ood_failures/  (the 20 NotALeaf images that received the
    highest tomato-class confidence — visual review reveals which negative
    types are missing from training)

Hard-fail gates (exit 1):
  - overall_accuracy < target_accuracy        (config: target_accuracy)
  - notaleaf_recall < notaleaf_min_recall     (config: notaleaf_min_recall)
  - false_reject_rate > max_false_reject_rate (config: max_false_reject_rate)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (classification_report, confusion_matrix,
                             f1_score, roc_auc_score, roc_curve)

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


def _ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == labels).astype(np.float32)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(labels)
    for i in range(n_bins):
        in_bin = (conf > bins[i]) & (conf <= bins[i + 1])
        if not in_bin.any():
            continue
        ece += (in_bin.sum() / n) * abs(
            conf[in_bin].mean() - correct[in_bin].mean())
    return float(ece)


def _brier(probs: np.ndarray, labels: np.ndarray) -> float:
    """Multi-class Brier score: mean squared error of probs vs one-hot."""
    n, k = probs.shape
    onehot = np.zeros_like(probs)
    onehot[np.arange(n), labels] = 1.0
    return float(((probs - onehot) ** 2).sum(axis=1).mean())


def _fpr_at_tpr(scores: np.ndarray, labels: np.ndarray,
                target_tpr: float = 0.95) -> float:
    """For binary scores (higher = positive class), FPR at the threshold
    that achieves at least target_tpr.
    """
    fpr, tpr, _ = roc_curve(labels, scores)
    # Find the smallest threshold giving tpr >= target_tpr.
    idx = np.searchsorted(tpr, target_tpr, side="left")
    if idx >= len(fpr):
        return 1.0
    return float(fpr[idx])


def _resolve_model_path(ckpt_dir: Path) -> Path:
    calibrated = ckpt_dir / "stage2_calibrated.keras"
    uncalibrated = ckpt_dir / "stage2_best.keras"
    if calibrated.exists():
        return calibrated
    if uncalibrated.exists():
        print(f"  >> WARN: {calibrated} not found — falling back to "
              f"{uncalibrated} (calibration step skipped).")
        return uncalibrated
    raise FileNotFoundError(
        f"Neither {calibrated} nor {uncalibrated} exists. "
        "Run train_stage2.py (and calibrate_temperature.py) first."
    )


def main() -> None:
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    banner_script("A7 Evaluation (11-class + OOD)", device)

    config = load_config()
    classes: list[str] = config["classes"]
    ood_class = (config.get("ood") or {}).get("class_name")
    ood_idx = classes.index(ood_class) if ood_class else None
    root = project_root()
    ckpt_path = _resolve_model_path(
        root / config["paths"]["checkpoints_dir"])
    results_dir = root / config["paths"]["results_dir"]
    report_path = results_dir / "eval_report.json"
    cm_path = results_dir / "confusion_matrix.png"
    failures_dir = results_dir / "ood_failures"

    banner_phase("Loading Model + Test Set")
    from utils.layers import get_temperature_scale_layer
    TemperatureScale = get_temperature_scale_layer()
    model = tf.keras.models.load_model(
        ckpt_path,
        custom_objects={"TemperatureScale": TemperatureScale},
        safe_mode=False,
    )
    test_csv = root / config["paths"]["splits_dir"] / "test.csv"
    test_ds = build_split_dataset(test_csv, config)
    df = pd.read_csv(test_csv)
    banner_step("LD-01", "Loaded",
                model=str(ckpt_path), test_samples=len(df))

    banner_phase("Running Inference")
    all_probs: list[np.ndarray] = []
    y_true: list[int] = []
    for batch_x, batch_y in test_ds:
        probs = model.predict(batch_x, verbose=0)
        all_probs.append(probs)
        y_true.extend(np.argmax(batch_y.numpy(), axis=1).tolist())
    probs = np.concatenate(all_probs, axis=0)
    y_true_np = np.asarray(y_true, dtype=np.int64)
    y_pred_np = probs.argmax(axis=1).astype(np.int64)

    banner_phase("Standard Metrics")
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
    banner_step("M-01", "Overall accuracy", accuracy=f"{overall_acc*100:.2f}%")
    banner_step("M-02", "Macro F1", macro_f1=f"{macro_f1:.4f}")
    for cls in classes:
        m = per_class[cls]
        banner_step(f"PC-{classes.index(cls):02d}", cls,
                    precision=f"{m['precision']:.3f}",
                    recall=f"{m['recall']:.3f}",
                    f1=f"{m['f1']:.3f}",
                    support=m["support"])

    banner_phase("Calibration Metrics")
    ece = _ece(probs, y_true_np)
    brier = _brier(probs, y_true_np)
    banner_step("CAL-01", "ECE / Brier", ece=f"{ece:.4f}", brier=f"{brier:.4f}")

    # ---- OOD metrics ---------------------------------------------------
    ood_metrics: dict = {}
    failures_paths: list[str] = []
    if ood_idx is not None:
        banner_phase("OOD Reject Class Metrics")
        # Binary view: is this a not-a-leaf?
        bin_true = (y_true_np == ood_idx).astype(np.int64)
        # Score: probability assigned to NotALeaf class. Higher → more "OOD".
        bin_score = probs[:, ood_idx]

        # Rejection recall = TP / (TP + FN) on the NotALeaf-positive class.
        # I.e. of all true negatives, how many did we correctly reject?
        notaleaf_recall = per_class[ood_class]["recall"]

        # False-reject rate = how often we incorrectly classify a real leaf
        # as NotALeaf. FRR = P(predicted=NotALeaf | true=any tomato class).
        tomato_mask = (y_true_np != ood_idx)
        if tomato_mask.any():
            frr = float((y_pred_np[tomato_mask] == ood_idx).mean())
        else:
            frr = 0.0

        # AUROC and FPR@95%TPR using NotALeaf probability as score.
        try:
            auroc = float(roc_auc_score(bin_true, bin_score))
        except ValueError:
            auroc = float("nan")
        fpr_at_95 = _fpr_at_tpr(bin_score, bin_true, target_tpr=0.95)

        # Confidence-threshold view: how often does the 0.60 threshold fire
        # per class, and what fraction is class-10's argmax probability?
        thresh = float(config.get("confidence_threshold", 0.6))
        per_class_low_conf = {}
        for cls_i, cls in enumerate(classes):
            mask = (y_pred_np == cls_i)
            if mask.any():
                low = float((probs[mask].max(axis=1) < thresh).mean())
            else:
                low = 0.0
            per_class_low_conf[cls] = low

        ood_metrics = {
            "notaleaf_recall": float(notaleaf_recall),
            "false_reject_rate": frr,
            "auroc_leaf_vs_notleaf": auroc,
            "fpr_at_95_tpr": fpr_at_95,
            "confidence_threshold": thresh,
            "fraction_below_threshold_per_class": per_class_low_conf,
        }
        banner_step("OOD-01", "Reject class behaviour",
                    notaleaf_recall=f"{notaleaf_recall*100:.2f}%",
                    false_reject_rate=f"{frr*100:.2f}%",
                    auroc=f"{auroc:.4f}",
                    fpr_at_95tpr=f"{fpr_at_95:.4f}")

        # Dump 20 hardest negative failures (true=NotALeaf, predicted=tomato
        # with high confidence) for visual review.
        if failures_dir.exists():
            shutil.rmtree(failures_dir)
        failures_dir.mkdir(parents=True, exist_ok=True)
        fn_mask = (y_true_np == ood_idx) & (y_pred_np != ood_idx)
        if fn_mask.any():
            tomato_probs = probs.copy()
            tomato_probs[:, ood_idx] = -1.0  # exclude OOD column
            hardness = tomato_probs.max(axis=1)
            ranked = np.where(fn_mask)[0][
                np.argsort(-hardness[fn_mask])][:20]
            for rank, i in enumerate(ranked):
                src = Path(df.iloc[int(i)]["filepath"])
                if not src.exists():
                    continue
                pred_cls = classes[int(y_pred_np[i])]
                dst = failures_dir / (
                    f"{rank:02d}_pred-{pred_cls}_p{hardness[i]:.2f}{src.suffix}"
                )
                try:
                    shutil.copy2(src, dst)
                    failures_paths.append(str(dst))
                except OSError as e:
                    print(f"  >> SKIP copy: {src} → {dst}  ({e})")
            banner_step("OOD-02", "Hard-negative failures dumped",
                        count=len(failures_paths), dir=str(failures_dir))

    banner_phase("Confusion Matrix")
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
        "ece": ece,
        "brier": brier,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "class_names": classes,
        "test_samples": int(len(df)),
        "model_checkpoint": str(ckpt_path),
        "ood": ood_metrics,
        "ood_failures_dumped": failures_paths,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    banner_step("RPT-01", "Eval report saved", path=str(report_path))

    # ---- Gates ---------------------------------------------------------
    target_acc = float(config["target_accuracy"])
    target_recall = float(config.get("notaleaf_min_recall", 0.0))
    max_frr = float(config.get("max_false_reject_rate", 1.0))

    failed = []
    if overall_acc < target_acc:
        failed.append(
            f"overall_accuracy={overall_acc:.4f} < target={target_acc:.4f}")
    if ood_metrics:
        nr = ood_metrics["notaleaf_recall"]
        frr = ood_metrics["false_reject_rate"]
        if nr < target_recall:
            failed.append(
                f"notaleaf_recall={nr:.4f} < required={target_recall:.4f}")
        if frr > max_frr:
            failed.append(
                f"false_reject_rate={frr:.4f} > allowed={max_frr:.4f}")

    if failed:
        print("\n[FAIL] One or more eval gates did not pass:")
        for f in failed:
            print(f"   - {f}")
        print("\n   Inspect:")
        print("     - per-class F1 in eval_report.json")
        print("     - ood_failures/ for negative-class blind spots")
        print("     - confusion_matrix.png for tomato/tomato confusions")
        sys.exit(1)

    print(f"\n[PASS] All eval gates passed.")
    print(f"   accuracy        : {overall_acc:.4f}  (>= {target_acc:.4f})")
    if ood_metrics:
        print(f"   notaleaf_recall : {ood_metrics['notaleaf_recall']:.4f}  "
              f"(>= {target_recall:.4f})")
        print(f"   false_reject    : {ood_metrics['false_reject_rate']:.4f}  "
              f"(<= {max_frr:.4f})")


if __name__ == "__main__":
    main()
