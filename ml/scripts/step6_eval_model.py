"""TomatoCare — Model Evaluation (11-Class + Out-Of-Distribution)
Evaluates accuracy, F1 score, Expected Calibration Error (ECE), and leaf gating robustness
on a held-out test dataset, ensuring model metrics satisfy Quality Assurance gates.
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





# ECE (Expected Calibration Error): Measures how well confidence percentages match real accuracy.
# It groups predictions into bins (e.g. 80-90% confidence) and compares bin accuracy to confidence.
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


# Brier Score: Measures prediction error (like Mean Squared Error for classification).
# It computes the squared difference between the predicted probabilities and true labels. Lower is better.
def _brier(probs: np.ndarray, labels: np.ndarray) -> float:
    """Multi-class Brier score: mean squared error of probs vs one-hot."""
    n, k = probs.shape
    onehot = np.zeros_like(probs)
    onehot[np.arange(n), labels] = 1.0
    return float(((probs - onehot) ** 2).sum(axis=1).mean())


# FPR at 95% TPR: Computes the False Positive Rate when we capture 95% of the real leaves.
# It shows how many invalid items leak through if the gate is set to be very sensitive.
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
        "Run step2_train_stage2.py (and step3_calibrate_temperature.py) first.")
def main() -> None:
    # STEP 1: Set seed for absolute reproducibility
    set_seed(42)

    import tensorflow as tf
    from utils.dataset_loader import build_split_dataset

    device = "cuda" if tf.config.list_physical_devices("GPU") else "cpu"
    print(f"--- TomatoCare — Evaluation (11-class + OOD) ({device}) ---")

    config = load_config()
    classes: list[str] = config["classes"]
    ood_class = (config.get("ood") or {}).get("class_name")
    ood_idx = classes.index(ood_class) if ood_class else None
    root = project_root()
    
    # STEP 2: Find the latest model (calibrated is preferred, uncalibrated is fallback)
    ckpt_path = _resolve_model_path(
        root / config["paths"]["checkpoints_dir"])
    results_dir = root / config["paths"]["results_dir"]
    report_path = results_dir / "eval_report.json"
    cm_path = results_dir / "confusion_matrix.png"
    failures_dir = results_dir / "ood_failures"

    print("--- Loading Model + Test Set ---")
    # STEP 3: Load the Keras model with our custom TemperatureScale division layer
    from utils.layers import TemperatureScale
    model = tf.keras.models.load_model(
        ckpt_path,
        custom_objects={"TemperatureScale": TemperatureScale},
        safe_mode=False,
    )
    # Load the test CSV and prepare the dataset iterator
    test_csv = root / config["paths"]["splits_dir"] / "test.csv"
    test_ds = build_split_dataset(test_csv, config)
    df = pd.read_csv(test_csv)
    print(f"Model loaded: {ckpt_path} | Test samples: {len(df)}")

    print("--- Running Inference ---")
    # STEP 4: Run predictions over all test dataset batches
    all_probs: list[np.ndarray] = []
    y_true: list[int] = []
    for batch_x, batch_y in test_ds:
        probs = model.predict(batch_x, verbose=0)
        all_probs.append(probs)
        y_true.extend(np.argmax(batch_y.numpy(), axis=1).tolist())
    probs = np.concatenate(all_probs, axis=0)
    y_true_np = np.asarray(y_true, dtype=np.int64)
    y_pred_np = probs.argmax(axis=1).astype(np.int64)

    print("--- Standard Metrics ---")
    # STEP 5: Compute macro accuracy, macro F1, and per-class precision/recall/F1 metrics
    # EXPLANATION FOR PRESENTATION: We test the model on a "held-out test set" (images the model has never 
    # seen before during training). This gives us the true, honest accuracy and F1 score of the system.
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
    print(f"Overall Accuracy: {overall_acc*100:.2f}%")
    print(f"Macro F1 Score: {macro_f1:.4f}")
    for cls in classes:
        m = per_class[cls]
        print(f"Class: {cls} | Precision: {m['precision']:.3f} | Recall: {m['recall']:.3f} | F1: {m['f1']:.3f} | Support: {m['support']}")

    print("--- Calibration Metrics ---")
    # STEP 6: Compute post-calibration ECE (Expected Calibration Error) and Brier Score
    ece = _ece(probs, y_true_np)
    brier = _brier(probs, y_true_np)
    print(f"ECE: {ece:.4f} | Brier score: {brier:.4f}")

    # ---- OOD metrics ---------------------------------------------------
    ood_metrics: dict = {}
    failures_paths: list[str] = []
    if ood_idx is not None:
        print("--- OOD Reject Class Metrics ---")
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
        print(f"OOD Recall: {notaleaf_recall*100:.2f}% | False Reject Rate: {frr*100:.2f}% | AUROC: {auroc:.4f} | FPR@95%TPR: {fpr_at_95:.4f}")

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
                    print(f"SKIP copy: {src} -> {dst} ({e})")
            print(f"Dumped {len(failures_paths)} hard-negative failures to: {failures_dir}")

    print("--- Generating Confusion Matrix ---")
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
    print(f"Confusion matrix saved to: {cm_path}")

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
    print(f"Evaluation report saved to: {report_path}")

    # ---- STEP 7: Quality Assurance / Hard Gates -------------------------
    # We define minimum performance targets (e.g. min accuracy) that the model
    # MUST satisfy to pass. If it fails these gates, the script exits with an error.
    target_acc = float(config["target_accuracy"])
    target_recall = float(config.get("notaleaf_min_recall", 0.0))
    max_frr = float(config.get("max_false_reject_rate", 1.0))

    failed = []
    # Check 1: Overall accuracy threshold (e.g. must be >= 90%)
    if overall_acc < target_acc:
        failed.append(
            f"overall_accuracy={overall_acc:.4f} < target={target_acc:.4f}")
    if ood_metrics:
        nr = ood_metrics["notaleaf_recall"]
        frr = ood_metrics["false_reject_rate"]
        # Check 2: Out-Of-Distribution recall (leaf gate must reject non-leaves)
        if nr < target_recall:
            failed.append(
                f"notaleaf_recall={nr:.4f} < required={target_recall:.4f}")
        # Check 3: False rejection rate (should not reject valid tomato leaves)
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
