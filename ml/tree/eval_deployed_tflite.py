"""Authoritative evaluation of the DEPLOYED TFLite cascade.

The WSL Keras checkpoints (tc_data/models/*.keras) no longer exist, so this
script evaluates the exact artifacts that ship in the Android app
(android/app/src/main/assets/*.tflite) against the held-out tomato test set
(ml/dataset/raw/tomato20k/valid). This is the most authoritative possible
"deployed model" measurement: it is literally what runs on the phone.

Outputs (single source of truth):
    ml/reports/eval_deployed.json          - all metrics + raw confusion matrix
    ml/reports/confusion_matrix_deployed.png - row-normalised heatmap

Run on Windows:  py ml/tree/eval_deployed_tflite.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf

tf.get_logger().setLevel("ERROR")

ROOT = Path(__file__).resolve().parents[2]            # .../TomatoCare
ASSETS = ROOT / "android" / "app" / "src" / "main" / "assets"
TESTDIR = ROOT / "ml" / "dataset" / "raw" / "tomato20k" / "valid"
OUTDIR = ROOT / "ml" / "reports"
IMG = 224
BATCH = 64

# raw tomato20k/valid folder name -> canonical class key (from build_dataset.py)
RAW2KEY = {
    "Bacterial_spot": "bacterial_spot",
    "Early_blight": "early_blight",
    "healthy": "healthy",
    "Late_blight": "late_blight",
    "Leaf_Mold": "leaf_mold",
    "powdery_mildew": "powdery_mildew",
    "Septoria_leaf_spot": "septoria_leaf_spot",
    "Spider_mites Two-spotted_spider_mite": "spider_mites",
    "Target_Spot": "target_spot",
    "Tomato_mosaic_virus": "mosaic_virus",
    "Tomato_Yellow_Leaf_Curl_Virus": "yellow_leaf_curl_virus",
}


def load_labels():
    lab = json.loads((ASSETS / "labels.json").read_text())
    stages = {s["stage"]: s for s in lab["stages"]}
    s3 = stages[3]["classes"]
    leaf_pass = stages[1]["classes"].index(stages[1]["pass_class"])
    tom_pass = stages[2]["classes"].index(stages[2]["pass_class"])
    return s3, leaf_pass, tom_pass


class TFL:
    def __init__(self, path: Path):
        self.it = tf.lite.Interpreter(model_path=str(path))
        self.inp = self.it.get_input_details()[0]
        self.out = self.it.get_output_details()[0]
        self.cur = None

    def __call__(self, x: np.ndarray) -> np.ndarray:
        x = x.astype(np.float32)
        if self.cur != x.shape:
            self.it.resize_tensor_input(self.inp["index"], x.shape)
            self.it.allocate_tensors()
            self.cur = x.shape
        self.it.set_tensor(self.inp["index"], x)
        self.it.invoke()
        return self.it.get_tensor(self.out["index"])


def ece_score(conf: np.ndarray, correct: np.ndarray, n_bins: int = 15) -> float:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    n = len(conf)
    e = 0.0
    for b in range(n_bins):
        m = (conf > edges[b]) & (conf <= edges[b + 1])
        if m.sum() > 0:
            e += abs(correct[m].mean() - conf[m].mean()) * m.sum() / n
    return float(e)


def save_png(cm: np.ndarray, names, path: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("[eval] matplotlib unavailable - PNG skipped (matrix is in JSON)")
        return
    cmn = cm.astype(float) / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(names))); ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Deployed Stage 3 - row-normalised confusion")
    for i in range(len(names)):
        for j in range(len(names)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        fontsize=6, color="black" if cmn[i, j] < 0.5 else "white")
    fig.colorbar(im, fraction=0.046, pad=0.04); fig.tight_layout()
    fig.savefig(path, dpi=150); plt.close(fig)
    print(f"[eval] confusion PNG -> {path}")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    s3_names, LEAF, TOM = load_labels()
    ncls = len(s3_names)

    ds = tf.keras.utils.image_dataset_from_directory(
        TESTDIR, labels="inferred", label_mode="int",
        image_size=(IMG, IMG), crop_to_aspect_ratio=True,
        batch_size=BATCH, shuffle=False)
    raw_names = ds.class_names
    missing = [r for r in raw_names if r not in RAW2KEY]
    if missing:
        sys.exit(f"[eval] unmapped folders: {missing}")
    ds2model = np.array([s3_names.index(RAW2KEY[r]) for r in raw_names])
    ds = ds.prefetch(tf.data.AUTOTUNE)

    leaf = TFL(ASSETS / "stage1_leaf_float16.tflite")
    tom = TFL(ASSETS / "stage2_tomato_float16.tflite")
    dis = TFL(ASSETS / "stage3_disease_float16.tflite")
    print(f"[eval] stage3 in={dis.inp['shape']} dtype={dis.inp['dtype']} "
          f"out={dis.out['shape']}")

    cm = np.zeros((ncls, ncls), dtype=int)
    yt_all, yp_all, conf_all, corr_all = [], [], [], []
    n_total = n_leaf = n_both = n_e2e = 0
    nb = 0
    for bx, by in ds:
        x = (tf.cast(bx, tf.float32) / 255.0).numpy()
        true_m = ds2model[by.numpy()]
        p3 = dis(x); dpred = p3.argmax(1); dconf = p3.max(1)
        is_leaf = leaf(x).argmax(1) == LEAF
        is_tom = tom(x).argmax(1) == TOM
        passed = is_leaf & is_tom
        for t, p in zip(true_m, dpred):
            cm[t, p] += 1
        yt_all.append(true_m); yp_all.append(dpred)
        conf_all.append(dconf); corr_all.append((dpred == true_m).astype(float))
        n_total += len(true_m); n_leaf += int(is_leaf.sum())
        n_both += int(passed.sum()); n_e2e += int((passed & (dpred == true_m)).sum())
        nb += 1
        if nb % 20 == 0:
            print(f"[eval] batch {nb} ({n_total} imgs)")

    yt = np.concatenate(yt_all); yp = np.concatenate(yp_all)
    conf = np.concatenate(conf_all); corr = np.concatenate(corr_all)
    acc3 = float((yt == yp).mean())
    per_class = {s3_names[i]: {
        "recall": round(float(((yt == i) & (yp == i)).sum() / max((yt == i).sum(), 1)), 4),
        "n": int((yt == i).sum())} for i in range(ncls)}

    report = {
        "_source": "DEPLOYED tflite cascade vs tomato20k/valid (held-out)",
        "test_set": str(TESTDIR),
        "n_test": int(n_total),
        "model_sizes_bytes": {
            "stage1": (ASSETS / "stage1_leaf_float16.tflite").stat().st_size,
            "stage2": (ASSETS / "stage2_tomato_float16.tflite").stat().st_size,
            "stage3": (ASSETS / "stage3_disease_float16.tflite").stat().st_size,
        },
        "stage3_disease": {
            "test_accuracy": round(acc3, 4),
            "ece_test_15bin": round(ece_score(conf, corr), 4),
            "per_class": per_class,
            "confusion_labels": s3_names,
            "confusion_matrix": cm.tolist(),
        },
        "end_to_end": {
            "n_tomato_test": n_total,
            "passed_leaf_gate_pct": round(100 * n_leaf / max(n_total, 1), 2),
            "passed_both_gates_pct": round(100 * n_both / max(n_total, 1), 2),
            "correct_diagnosis_pct": round(100 * n_e2e / max(n_total, 1), 2),
        },
    }
    total_mb = sum(report["model_sizes_bytes"].values()) / 1e6
    report["model_total_mb"] = round(total_mb, 2)

    (OUTDIR / "eval_deployed.json").write_text(json.dumps(report, indent=2))
    save_png(cm, s3_names, OUTDIR / "confusion_matrix_deployed.png")

    print("\n================ DEPLOYED CASCADE — GROUND TRUTH ================")
    print(f"Stage 3 disease accuracy : {acc3*100:.2f}%   (n={n_total})")
    print(f"Stage 3 test ECE (15-bin): {report['stage3_disease']['ece_test_15bin']}")
    print(f"End-to-end correct dx    : {report['end_to_end']['correct_diagnosis_pct']}%")
    print(f"Passed leaf gate         : {report['end_to_end']['passed_leaf_gate_pct']}%")
    print(f"Passed both gates        : {report['end_to_end']['passed_both_gates_pct']}%")
    print(f"Total model size         : {total_mb:.2f} MB")
    print("Per-class recall:")
    for k, v in per_class.items():
        print(f"   {k:<24} {v['recall']:.4f}  (n={v['n']})")
    print("================================================================")


if __name__ == "__main__":
    main()
