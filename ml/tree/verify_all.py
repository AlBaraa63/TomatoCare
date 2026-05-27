"""verify_all.py — one-shot re-measurement & consistency check for the deployed cascade.

Two modes, selected automatically:

  FULL EVAL  — if the held-out test set is present at ml/dataset/raw/tomato20k/valid,
               re-runs the deployed TFLite cascade end-to-end (delegates to
               eval_deployed_tflite.py), regenerating eval_deployed.json +
               confusion_matrix_deployed.png, then diffs the fresh numbers against the
               committed JSON and audits them.

  AUDIT      — if the dataset is absent (the current state), independently recomputes
               every *derivable* metric — overall accuracy, per-class recall, per-class
               sample counts, and total model size — from the committed eval_deployed.json
               and the on-disk .tflite files, and asserts they match the stored summary.
               (ECE depends on per-sample confidences, so it can only be re-verified by a
               FULL EVAL once the dataset is restored.)

Run:  py ml/tree/verify_all.py        (exit code 0 = all checks passed, 1 = a check failed)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "ml" / "reports"
ASSETS = ROOT / "android" / "app" / "src" / "main" / "assets"
TESTDIR = ROOT / "ml" / "dataset" / "raw" / "tomato20k" / "valid"
JSON = REPORTS / "eval_deployed.json"
EVAL_SCRIPT = ROOT / "ml" / "tree" / "eval_deployed_tflite.py"

_fails = 0


def check(label: str, cond: bool, got=None, want=None) -> bool:
    global _fails
    if not cond:
        _fails += 1
    status = "PASS" if cond else "FAIL"
    extra = ""
    if not cond and (got is not None or want is not None):
        extra = f"   (got {got!r}, expected {want!r})"
    print(f"  [{status}] {label}{extra}")
    return cond


def audit(data: dict) -> None:
    print("\n=== AUDIT MODE — re-deriving every metric computable without the dataset ===")
    s3 = data["stage3_disease"]
    labels = s3["confusion_labels"]
    cm = s3["confusion_matrix"]
    n = len(labels)

    check(f"confusion matrix is {n}x{n}", len(cm) == n and all(len(r) == n for r in cm))

    total = sum(sum(r) for r in cm)
    check("matrix total == n_test", total == data["n_test"], total, data["n_test"])

    print("  per-class recall + n (recomputed from the matrix vs stored):")
    for i, lab in enumerate(labels):
        row = sum(cm[i])
        rec = round(cm[i][i] / row, 4) if row else 0.0
        stored_rec = s3["per_class"][lab]["recall"]
        stored_n = s3["per_class"][lab]["n"]
        check(f"    {lab:<24} recall {rec:.4f}", abs(rec - stored_rec) <= 1e-4, rec, stored_rec)
        check(f"    {lab:<24} n {row}", row == stored_n, row, stored_n)

    correct = sum(cm[i][i] for i in range(n))
    acc = round(correct / total, 4) if total else 0.0
    check(f"overall accuracy {acc:.4f} ({correct}/{total}) == test_accuracy",
          abs(acc - s3["test_accuracy"]) <= 1e-4, acc, s3["test_accuracy"])

    print("  model file sizes (on disk vs stored in JSON):")
    files = {
        "stage1": ASSETS / "stage1_leaf_float16.tflite",
        "stage2": ASSETS / "stage2_tomato_float16.tflite",
        "stage3": ASSETS / "stage3_disease_float16.tflite",
    }
    total_bytes = 0
    for key, fp in files.items():
        if not fp.exists():
            check(f"    {key} file present", False, "missing", str(fp))
            continue
        sz = fp.stat().st_size
        total_bytes += sz
        check(f"    {key} size {sz} B", sz == data["model_sizes_bytes"][key],
              sz, data["model_sizes_bytes"][key])
    total_mb = round(total_bytes / 1e6, 2)
    check(f"    total size {total_mb} MB == model_total_mb",
          abs(total_mb - data["model_total_mb"]) <= 0.01, total_mb, data["model_total_mb"])

    print("\n  NOTE: ECE (reported 0.061) needs per-sample confidences and cannot be re-derived")
    print("        from the matrix. Restore the test set and re-run for a FULL EVAL to confirm it.")


def full_eval(committed: dict) -> None:
    print("\n=== FULL EVAL MODE — dataset present, re-running the deployed cascade ===")
    print(f"  running: {sys.executable} {EVAL_SCRIPT}")
    r = subprocess.run([sys.executable, str(EVAL_SCRIPT)], cwd=str(ROOT))
    if r.returncode != 0:
        check("eval_deployed_tflite.py exited 0", False)
        return
    fresh = json.loads(JSON.read_text())
    c, f = committed["stage3_disease"], fresh["stage3_disease"]
    check("disease accuracy reproduces", c["test_accuracy"] == f["test_accuracy"],
          f["test_accuracy"], c["test_accuracy"])
    check("ECE reproduces", c["ece_test_15bin"] == f["ece_test_15bin"],
          f["ece_test_15bin"], c["ece_test_15bin"])
    check("end-to-end reproduces",
          committed["end_to_end"]["correct_diagnosis_pct"] == fresh["end_to_end"]["correct_diagnosis_pct"],
          fresh["end_to_end"]["correct_diagnosis_pct"],
          committed["end_to_end"]["correct_diagnosis_pct"])
    audit(fresh)


def main() -> None:
    if not JSON.exists():
        print(f"[FAIL] {JSON} not found — nothing to verify.")
        sys.exit(1)
    data = json.loads(JSON.read_text())
    print(f"Source of truth : {JSON}")
    print(f"_source         : {data.get('_source')}")
    print(f"test set        : {TESTDIR}")

    dataset_present = TESTDIR.exists() and any(TESTDIR.iterdir())
    if dataset_present:
        full_eval(data)
    else:
        print("\n[info] test set NOT on disk -> AUDIT MODE (re-derive everything computable).")
        audit(data)

    print("\n" + "=" * 64)
    print("RESULT:", "ALL CHECKS PASSED" if _fails == 0 else f"{_fails} CHECK(S) FAILED")
    print("=" * 64)
    sys.exit(1 if _fails else 0)


if __name__ == "__main__":
    main()
