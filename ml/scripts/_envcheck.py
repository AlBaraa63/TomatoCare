"""Throwaway environment check — confirms TF sees the GPU inside the WSL venv."""
import tensorflow as tf

print("TF version  :", tf.__version__)
gpus = tf.config.list_physical_devices("GPU")
print("GPUs found  :", len(gpus))
for g in gpus:
    print("  ", g.name)

if gpus:
    with tf.device("/GPU:0"):
        a = tf.random.uniform((2048, 2048))
        c = tf.matmul(a, a)
        _ = c.numpy()
    print("GPU matmul  : OK")
else:
    print("GPU matmul  : SKIPPED (no GPU visible to TF)")
