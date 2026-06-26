"""TomatoCare — TFLite Model Export
Converts the calibrated Keras model to TensorFlow Lite float16 format, 
and validates output size, tensor shapes, and accuracy metrics before deployment.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.seed import load_config, project_root, set_seed  # noqa: E402





# Reads a raw image, resizes it to 224x224, and normalizes pixel values to [0, 1] for testing the TFLite model
def _preprocess_image(path: str, img_size: int) -> np.ndarray:
    img = Image.open(path).convert("RGB").resize(
        (img_size, img_size), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr


def main() -> None:
    set_seed(42)
    import tensorflow as tf

    print("--- TomatoCare — TFLite Float16 Export ---")

    config = load_config()
    root = project_root()
    ckpt_dir = root / config["paths"]["checkpoints_dir"]
    calibrated = ckpt_dir / "stage2_calibrated.keras"
    uncalibrated = ckpt_dir / "stage2_best.keras"
    if calibrated.exists():
        keras_ckpt = calibrated
    elif uncalibrated.exists():
        print(f"  >> WARN: {calibrated} not found — exporting uncalibrated "
              f"model from {uncalibrated}.")
        keras_ckpt = uncalibrated
    else:
        raise FileNotFoundError(
            f"Neither {calibrated} nor {uncalibrated} exists. "
            "Run step2_train_stage2.py (and step3_calibrate_temperature.py)."
        )
    tflite_dir = root / config["paths"]["tflite_dir"]
    tflite_dir.mkdir(parents=True, exist_ok=True)
    tflite_path = tflite_dir / "tomatocare_model_float16.tflite"
    results_dir = root / config["paths"]["results_dir"]
    export_report = results_dir / "tflite_export_report.json"
    keras_eval = results_dir / "eval_report.json"

    if not keras_eval.exists():
        raise FileNotFoundError(
            f"{keras_eval} not found. Run eval_model.py first."
        )

    print("--- Converting to TFLite (float16) ---")
    from utils.layers import TemperatureScale
    model = tf.keras.models.load_model(
        keras_ckpt,
        custom_objects={"TemperatureScale": TemperatureScale},
        safe_mode=False,
    )
    
    # STEP 2: Configure the TFLite Converter to optimize and use float16 precision
    # EXPLANATION FOR PRESENTATION: We convert the model to TensorFlow Lite format for Android. 
    # We use Float16 Quantization, which changes 32-bit floats to 16-bit floats. This cuts the model 
    # file size in half (from ~20MB to under 10MB) so it can run fast on budget mobile devices.
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    t0 = time.time()
    tflite_bytes = converter.convert()
    dt = time.time() - t0
    tflite_path.write_bytes(tflite_bytes)
    size_mb = tflite_path.stat().st_size / (1024 * 1024)
    print(f"Converted model in {dt:.1f}s | Size: {size_mb:.2f} MB | Saved to: {tflite_path}")

    print("--- Checking Size Gate ---")
    # STEP 3: Verify the file size fits within requirements (e.g. <= 15MB limit)
    limit_mb = config["tflite_max_size_mb"]
    if size_mb > limit_mb:
        print(f"[FAIL] .tflite size {size_mb:.2f} MB > limit {limit_mb} MB.")
        print("       Try int8 quantisation, smaller backbone, or pruning.")
        sys.exit(1)
    print(f"  >> PASS: {size_mb:.2f} MB <= {limit_mb} MB limit.")

    print("--- Post-Export Accuracy Check ---")
    # STEP 4: Setup TFLite interpreter to simulate mobile execution
    test_csv = root / config["paths"]["splits_dir"] / "test.csv"
    df = pd.read_csv(test_csv)

    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]
    img_size = config["img_size"]

    # STEP 5: Verify input/output shapes match the Android contract (e.g. [1, 224, 224, 3] and [1, 11])
    # This acts as a compiler check before deployment.
    expected_output = (1, len(config["classes"]))
    actual_output = tuple(int(d) for d in out["shape"])
    expected_input = (1, img_size, img_size, 3)
    actual_input = tuple(int(d) for d in inp["shape"])
    if actual_output != expected_output:
        print(f"[FAIL] TFLite output shape {actual_output} != "
              f"expected {expected_output}.")
        sys.exit(1)
    if actual_input != expected_input:
        print(f"[FAIL] TFLite input shape {actual_input} != "
              f"expected {expected_input}.")
        sys.exit(1)
    print(f"  >> PASS: input {actual_input}, output {actual_output} match "
          "Android contract.")

    # STEP 6: Run inference using the TFLite Interpreter to verify accuracy
    correct = 0
    inference_times: list[float] = []
    for _, row in df.iterrows():
        x = _preprocess_image(row["filepath"], img_size)
        x = np.expand_dims(x, 0).astype(inp["dtype"])
        interpreter.set_tensor(inp["index"], x)
        t1 = time.time()
        interpreter.invoke()
        inference_times.append((time.time() - t1) * 1000.0)
        probs = interpreter.get_tensor(out["index"])[0]
        if int(np.argmax(probs)) == int(row["class_index"]):
            correct += 1

    tflite_acc = correct / max(len(df), 1)
    mean_ms = float(np.mean(inference_times)) if inference_times else 0.0

    with open(keras_eval, "r", encoding="utf-8") as f:
        keras_acc = float(json.load(f)["overall_accuracy"])

    drop = keras_acc - tflite_acc
    print(f"Accuracy: Keras={keras_acc*100:.2f}% | TFLite={tflite_acc*100:.2f}% (Drop: {drop*100:+.2f}pp) | Inference: {mean_ms:.1f} ms")

    if drop > 0.01:
        print(f"[WARN] Accuracy drop {drop*100:.2f}pp > 1.0pp. "
              "Inspect class-specific drops before shipping.")

    report = {
        "source_keras_checkpoint": str(keras_ckpt),
        "calibrated": (keras_ckpt.name == "stage2_calibrated.keras"),
        "model_version": config.get("model_version", "unknown"),
        "num_classes": len(config["classes"]),
        "input_shape": list(actual_input),
        "output_shape": list(actual_output),
        "keras_accuracy": keras_acc,
        "tflite_accuracy": tflite_acc,
        "accuracy_drop": drop,
        "model_size_mb": size_mb,
        "size_limit_mb": limit_mb,
        "avg_inference_ms_cpu": mean_ms,
        "quantisation": "float16",
        "tflite_path": str(tflite_path),
    }
    with open(export_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Export report saved to: {export_report}")

    print(f"\nTFLite artifact ready. Copy it to your Android asset folder:\n   cp {tflite_path} android/app/src/main/assets/")


if __name__ == "__main__":
    main()
