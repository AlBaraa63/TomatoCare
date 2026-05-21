# ── TomatoCare ML pipeline ────────────────────────────────────────────────────
# CPU default. For GPU pass: --build-arg BASE_IMAGE=tensorflow/tensorflow:2.15.0-gpu
ARG BASE_IMAGE=tensorflow/tensorflow:2.15.0
FROM ${BASE_IMAGE}

WORKDIR /app

# TF is already in the base image — install only the extras
RUN pip install --no-cache-dir \
    "numpy>=1.24,<2.0" \
    "pillow>=10.0" \
    "scikit-learn>=1.3" \
    "matplotlib>=3.7" \
    "seaborn>=0.13" \
    "tqdm>=4.66" \
    "pyyaml>=6.0" \
    "pandas>=2.0" \
    "scipy>=1.10" \
    "tensorflow-datasets>=4.9"

COPY ml/ ml/

# Dataset, checkpoints, and results are mounted at runtime (see docker-compose.yml)
VOLUME ["/app/ml/dataset", "/app/ml/models", "/app/ml/results"]

ENV TF_CPP_MIN_LOG_LEVEL=2
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "ml.scripts.eval_model"]
