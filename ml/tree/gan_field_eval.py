"""GAN fold-in field eval: does +600 synthetic bacterial_spot help on real photos?

Holds the deployed gates (stage1, stage2) CONSTANT and swaps only stage3 across
three variants:
    deployed  = currently-shipped stage3 (android assets)
    ctrl      = stage3 retrained minimal-aug, NO gan  (the fair control)
    gan       = stage3 retrained minimal-aug, +600 gan bacterial_spot

The clean comparison is ctrl-vs-gan (identical recipe, only the synthetic data
differs). Focus metric: bacterial_spot field recall (deployed baseline was 3/9).
"""
import json
from pathlib import Path
import numpy as np
import tensorflow as tf

H = Path.home()
PD = H / "tc_data" / "_img" / "plantdoc"
ASSETS = Path("/mnt/c/Users/POTATO/Desktop/TomatoCare/android/app/src/main/assets")
IMG = 224
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

DISEASE = ["bacterial_spot", "early_blight", "healthy", "late_blight", "leaf_mold",
           "mosaic_virus", "powdery_mildew", "septoria_leaf_spot", "spider_mites",
           "target_spot", "yellow_leaf_curl_virus"]
TOMATO_MAP = {
    "Tomato_leaf": "healthy", "Tomato_Early_blight_leaf": "early_blight",
    "Tomato_leaf_bacterial_spot": "bacterial_spot", "Tomato_leaf_late_blight": "late_blight",
    "Tomato_leaf_mosaic_virus": "mosaic_virus", "Tomato_leaf_yellow_virus": "yellow_leaf_curl_virus",
    "Tomato_mold_leaf": "leaf_mold", "Tomato_Septoria_leaf_spot": "septoria_leaf_spot",
    "Tomato_two_spotted_spider_mites_leaf": "spider_mites",
}
LEAF_IDX, TOMATO_IDX = 0, 1

STAGE3 = {
    "deployed": ASSETS / "stage3_disease_float16.tflite",
    "ctrl": H / "tc_data" / "tflite_ctrl" / "stage3_disease_float16.tflite",
    "gan": H / "tc_data" / "tflite_gan" / "stage3_disease_float16.tflite",
}


def decode(path):
    raw = tf.io.read_file(str(path))
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    shape = tf.shape(img)
    s = tf.minimum(shape[0], shape[1])
    img = tf.image.resize_with_crop_or_pad(img, s, s)
    img = tf.image.resize(img, [IMG, IMG])
    return (tf.cast(img, tf.float32) / 255.0).numpy().reshape(1, IMG, IMG, 3).astype(np.float32)


def load_imgs(root):
    items = []
    if not root.is_dir():
        return items
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name in TOMATO_MAP:
            for p in d.iterdir():
                if p.suffix.lower() in EXTS:
                    items.append((p, TOMATO_MAP[d.name]))
    return items


def interp(path):
    it = tf.lite.Interpreter(model_path=str(path)); it.allocate_tensors()
    return it


def run(it, x):
    i = it.get_input_details()[0]; o = it.get_output_details()[0]
    it.set_tensor(i["index"], x); it.invoke()
    return it.get_tensor(o["index"])[0]


def evaluate(name, leaf, tom, dis, items):
    n = len(items); passed_both = correct = 0
    per_class = {}
    for p, true in items:
        x = decode(p)
        pc = per_class.setdefault(true, {"n": 0, "correct": 0})
        pc["n"] += 1
        if int(np.argmax(run(leaf, x))) != LEAF_IDX:
            continue
        if int(np.argmax(run(tom, x))) != TOMATO_IDX:
            continue
        passed_both += 1
        if DISEASE[int(np.argmax(run(dis, x)))] == true:
            correct += 1; pc["correct"] += 1
    print(f"\n===== {name} =====")
    print(f"  end-to-end correct: {100*correct/max(n,1):.1f}%   ({correct}/{n})")
    print(f"  disease acc (on {passed_both} passed): {100*correct/max(passed_both,1):.1f}%")
    for k in sorted(per_class):
        pc = per_class[k]
        star = "  <-- GAN target" if k == "bacterial_spot" else ""
        print(f"     {k:26s} {pc['correct']:3d}/{pc['n']:<3d}{star}")
    return {"end_to_end_pct": round(100*correct/max(n, 1), 1),
            "bacterial_spot": per_class.get("bacterial_spot", {})}


test_items = load_imgs(PD / "test")
all_items = test_items + load_imgs(PD / "train")
print(f"PlantDoc field -> test:{len(test_items)}  train+test:{len(all_items)}")

leaf = interp(ASSETS / "stage1_leaf_float16.tflite")
tom = interp(ASSETS / "stage2_tomato_float16.tflite")

res = {}
for split_name, items in [("TEST", test_items), ("TRAIN+TEST", all_items)]:
    if not items:
        continue
    print(f"\n############ SPLIT: {split_name} (n={len(items)}) ############")
    for variant, path in STAGE3.items():
        if not Path(path).exists():
            print(f"[skip] {variant}: missing {path}")
            continue
        res[f"{variant}/{split_name}"] = evaluate(
            f"{variant.upper()} stage3  [{split_name}]", leaf, tom, interp(path), items)

Path("/mnt/c/Users/POTATO/AppData/Local/Temp/tc_gan_field_eval.json").write_text(json.dumps(res, indent=2))
print("\nDONE")
