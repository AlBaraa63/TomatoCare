"""TREE / export — convert trained .keras stage models to float16 TFLite.

For each stage we:
  1. Convert the Keras model to TFLite with float16 weight quantisation
     (same scheme as v1: ~2x smaller, negligible accuracy loss, still a
     float32 input/output interface so the Android side is unchanged).
  2. Run a parity check: feed the SAME random [0,1] tensor through the Keras
     model and the TFLite interpreter and report the max abs difference.
     This is the early-warning that preprocessing/quantisation didn't drift.

Output:  <out>/<stage>_float16.tflite  +  <out>/export_report.json

Run inside the WSL venv:
    python ml/tree/export.py                 # all stages found
    python ml/tree/export.py --stage stage3_disease
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

IMG = 224


def convert_one(keras_path: Path, out_path: Path) -> dict:
    model = tf.keras.models.load_model(keras_path)
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.target_spec.supported_types = [tf.float16]
    tflite = conv.convert()
    out_path.write_bytes(tflite)

    # ---- parity check: Keras vs TFLite on identical [0,1] input ----
    rng = np.random.default_rng(0)
    x = rng.random((1, IMG, IMG, 3), dtype=np.float32)  # already in [0,1]
    keras_out = model.predict(x, verbose=0)[0]

    interp = tf.lite.Interpreter(model_content=tflite)
    interp.allocate_tensors()
    inp = interp.get_input_details()[0]
    outp = interp.get_output_details()[0]
    interp.set_tensor(inp["index"], x)
    interp.invoke()
    tfl_out = interp.get_tensor(outp["index"])[0]

    max_abs_diff = float(np.max(np.abs(keras_out - tfl_out)))
    return {
        "keras_path": str(keras_path),
        "tflite_path": str(out_path),
        "size_mb": round(out_path.stat().st_size / (1024 * 1024), 3),
        "input_shape": [int(d) for d in inp["shape"]],
        "output_shape": [int(d) for d in outp["shape"]],
        "keras_top": int(np.argmax(keras_out)),
        "tflite_top": int(np.argmax(tfl_out)),
        "max_abs_diff": max_abs_diff,
        "parity_ok": bool(max_abs_diff < 1e-2 and
                          np.argmax(keras_out) == np.argmax(tfl_out)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=str(Path.home() / "tc_data" / "models"))
    ap.add_argument("--out", default=str(Path.home() / "tc_data" / "tflite"))
    ap.add_argument("--stage", default=None,
                    help="Single stage; default = every *.keras in --models")
    args = ap.parse_args()

    models_dir = Path(args.models)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.stage:
        keras_files = [models_dir / f"{args.stage}.keras"]
    else:
        keras_files = sorted(f for f in models_dir.glob("*.keras")
                             if "uncalibrated" not in f.stem)

    report = {}
    total_mb = 0.0
    for kf in keras_files:
        if not kf.exists():
            print(f"[skip] missing {kf}")
            continue
        stage = kf.stem
        info = convert_one(kf, out_dir / f"{stage}_float16.tflite")
        report[stage] = info
        total_mb += info["size_mb"]
        flag = "OK" if info["parity_ok"] else "!! PARITY DRIFT"
        print(f"{stage:<16} {info['size_mb']:.2f} MB  "
              f"diff={info['max_abs_diff']:.2e}  {flag}")

    report["_total_size_mb"] = round(total_mb, 3)
    (out_dir / "export_report.json").write_text(json.dumps(report, indent=2))
    print(f"\n[done] 3-model total = {total_mb:.2f} MB "
          f"(NFR-04 budget: 15 MB)  ->  {out_dir}")


if __name__ == "__main__":
    main()
