#!/usr/bin/env bash
# Sets up a torch venv for segment_leaves.py (MobileSAM zero-shot leaf masking).
# CPU wheels keep it small for smoke-testing; swap the index-url for a CUDA
# build to process the full farm fast.
set -e
VENV="$HOME/.venvs/seg-wsl"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
# CPU-only torch/torchvision (~200 MB vs ~2 GB CUDA). For the full run on GPU,
# reinstall from https://download.pytorch.org/whl/cu121 instead.
"$VENV/bin/pip" install --index-url https://download.pytorch.org/whl/cpu torch torchvision
"$VENV/bin/pip" install timm pillow numpy
echo "DONE: seg venv ready at $VENV"
