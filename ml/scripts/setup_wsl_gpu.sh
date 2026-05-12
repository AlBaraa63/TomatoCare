#!/usr/bin/env bash
# ============================================================
#  TomatoCare — WSL2 + CUDA + TensorFlow bootstrap
#  One-shot script. Idempotent (skips work that's already done).
#  Run from inside WSL: bash ml/scripts/setup_wsl_gpu.sh
# ============================================================
set -euo pipefail

banner_phase() {
    echo "=============================================================="
    echo "  PHASE: $1"
    echo "=============================================================="
}
banner_step() {
    echo "--------------------------------------------------------------"
    echo "  $1"
    echo "--------------------------------------------------------------"
}
fail() { echo "[FATAL] $*" >&2; exit 1; }

echo "##############################################################"
echo "  TomatoCare — WSL GPU Bootstrap"
echo "  Target  : Ubuntu 22.04 + Python 3.10 + TF 2.15.1 + CUDA 12.x"
echo "##############################################################"

# ---- Phase 1: environment sanity ----------------------------
banner_phase "Environment Sanity"
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    fail "This script must run inside WSL. From PowerShell: wsl -d Ubuntu-22.04"
fi
banner_step "Running inside WSL: OK"

if ! command -v nvidia-smi >/dev/null 2>&1; then
    fail "nvidia-smi not found in WSL. Update your Windows NVIDIA driver to >=535 — GPU passthrough requires it."
fi
banner_step "GPU passthrough check"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || \
    fail "nvidia-smi failed. Reboot Windows and try again."

# ---- Phase 2: system packages -------------------------------
banner_phase "System Packages"
PYTHON_BIN=python3.10
NEED_APT=0
command -v "$PYTHON_BIN" >/dev/null 2>&1 || NEED_APT=1
"$PYTHON_BIN" -c "import ensurepip" 2>/dev/null || NEED_APT=1
dpkg -s python3.10-venv >/dev/null 2>&1 || NEED_APT=1
if [ "$NEED_APT" = "1" ]; then
    banner_step "Installing Python 3.10 + venv + pip (apt)"
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        python3.10 python3.10-venv python3.10-dev python3-pip build-essential
fi
banner_step "Python 3.10 ready: $($PYTHON_BIN --version)"

# ---- Phase 3: project venv ----------------------------------
banner_phase "Project venv"
# Resolve project root regardless of cwd. We need it later for requirements.txt.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# IMPORTANT: venv must live on the Linux filesystem (ext4), NOT under /mnt/c.
# python -m venv on NTFS frequently produces a broken venv: missing
# bin/activate, ensurepip fails silently, site-packages stays empty. That's
# because pip's bootstrap relies on os.symlink semantics that NTFS via 9P
# doesn't honour. ~/.venvs/tomatocare-wsl sidesteps the whole class of bug.
VENV="$HOME/.venvs/tomatocare-wsl"
mkdir -p "$(dirname "$VENV")"

# Detect a stale broken venv (no activate script) and rebuild it.
if [ -d "$VENV" ] && [ ! -f "$VENV/bin/activate" ]; then
    banner_step "Removing broken venv at $VENV (no bin/activate found)"
    rm -rf "$VENV"
fi

# Also clean up the deprecated in-project venv if it exists, so the user
# doesn't have two competing trees.
LEGACY_VENV="$PROJECT_ROOT/ml/.venv-wsl"
if [ -d "$LEGACY_VENV" ]; then
    banner_step "Removing legacy venv at $LEGACY_VENV (use $VENV instead)"
    rm -rf "$LEGACY_VENV"
fi

if [ ! -d "$VENV" ]; then
    banner_step "Creating venv at $VENV"
    "$PYTHON_BIN" -m venv "$VENV"
else
    banner_step "venv already exists at $VENV"
fi

if [ ! -f "$VENV/bin/activate" ]; then
    fail "venv creation failed — $VENV/bin/activate is missing. Check apt logs."
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
banner_step "Activated venv: $(python --version)"

python -m pip install --upgrade pip wheel setuptools >/dev/null

# ---- Phase 4: project deps + TF GPU -------------------------
banner_phase "Installing Python Packages"
banner_step "Project requirements"
pip install -r "$PROJECT_ROOT/ml/requirements.txt" --progress-bar on
banner_step "TF wheels (CUDA + cuDNN bundled, ~1.5 GB download — this may take 10-15 min)"
# Force re-resolve in case the requirements.txt marker didn't pick up tensorflow[and-cuda].
pip install "tensorflow[and-cuda]==2.15.1" --progress-bar on

# ---- Phase 5: verify GPU -------------------------------------
banner_phase "GPU Verification"
python - <<'PY'
import tensorflow as tf
print(f"  TF version : {tf.__version__}")
gpus = tf.config.list_physical_devices('GPU')
print(f"  GPUs found : {len(gpus)}")
for g in gpus:
    print(f"    {g.name}")
if not gpus:
    raise SystemExit(
        "\n[FATAL] TF cannot see GPU. Common causes:\n"
        "  - WSL Ubuntu version mismatch (use 22.04, not 20.04)\n"
        "  - Old NVIDIA driver (Windows host needs >=535)\n"
        "  - Missing libcudnn — pip install --force-reinstall tensorflow[and-cuda]==2.15.1\n"
    )

# Quick smoke: matmul on GPU and confirm placement.
with tf.device('/GPU:0'):
    a = tf.random.uniform((1024, 1024))
    b = tf.random.uniform((1024, 1024))
    c = tf.matmul(a, b)
    _ = c.numpy()  # forces compute
print("  Smoke test : 1024x1024 matmul on GPU:0 — OK")
PY

# ---- Phase 6: next steps -------------------------------------
echo
echo "##############################################################"
echo "  WSL GPU setup complete."
echo "##############################################################"
echo
echo "Activate the venv in any new shell:"
echo "  source ~/.venvs/tomatocare-wsl/bin/activate"
echo
echo "Run the pipeline from project root (A3 may already be done):"
echo "  cd $PROJECT_ROOT"
echo "  python ml/scripts/prepare_plantvillage.py   # regenerates CSVs with WSL paths"
echo "  python ml/scripts/augment_uae.py            # A3"
echo "  python ml/scripts/train_stage1.py           # A5"
echo "  python ml/scripts/train_stage2.py           # A6"
echo "  python ml/scripts/eval_model.py             # A7 (gates accuracy >= 90%)"
echo "  python ml/scripts/export_tflite.py          # A8"
echo
echo "Note: if you previously ran A2 from Windows, the CSVs in"
echo "  ml/dataset/splits/ contain C:\\... paths that TF cannot read"
echo "  from WSL. Delete that directory before running A2 again."
echo
