#!/usr/bin/env bash
set -e
PY=/home/albaraa/.venvs/tomatocare-wsl/bin/python
T=/mnt/c/Users/POTATO/Desktop/TomatoCare/ml/tree
S3=/home/albaraa/tc_data/stage3_disease/train/bacterial_spot
GAN=/home/albaraa/tc_data/gan/bacterial_spot/generated

echo "===== [1/5] CONTROL: stage3 minimal-aug, NO gan ====="
"$PY" "$T/train.py" --stage stage3_disease --aug minimal --out /home/albaraa/tc_data/models_ctrl
"$PY" "$T/export.py" --stage stage3_disease --models /home/albaraa/tc_data/models_ctrl --out /home/albaraa/tc_data/tflite_ctrl

echo "===== [2/5] fold-in 600 GAN images as symlinks ====="
for f in "$GAN"/*.png; do ln -sf "$f" "$S3/gan_$(basename "$f")"; done
echo "bacterial_spot now: $(ls "$S3" | wc -l) files"

echo "===== [3/5] TREATMENT: stage3 minimal-aug, +gan ====="
"$PY" "$T/train.py" --stage stage3_disease --aug minimal --out /home/albaraa/tc_data/models_gan
"$PY" "$T/export.py" --stage stage3_disease --models /home/albaraa/tc_data/models_gan --out /home/albaraa/tc_data/tflite_gan

echo "===== [4/5] remove GAN symlinks (restore clean farm) ====="
find "$S3" -name 'gan_*' -type l -delete
echo "bacterial_spot restored: $(ls "$S3" | wc -l) files"

echo "===== [5/5] DONE ====="
echo "FOLDIN DONE"
