"""TREE / GAN — DCGAN for synthetic tomato-leaf generation (Armagan's idea).

Context: Dr. Armagan Elibol suggested generating synthetic leaf images (cf.
raj-shah14/Synthetic-Leaf-Generation-Using-GAN-and-Classification-using-CNN)
to expand the dataset for weak classes. This is a clean DCGAN that learns one
class's images and emits synthetic samples.

Honest framing (per the field-validation finding): synthetic data is a TRAINING
aid, not a validation set. After generating, we fold the samples into stage3
training, retrain, and re-run the SAME real-field eval to measure whether it
actually helps — same rigour we applied to the augmentation experiment.

  python ml/tree/gan_dcgan.py \
      --class-dir ~/tc_data/stage3_disease/train/bacterial_spot \
      --out ~/tc_data/gan/bacterial_spot --epochs 150 --n-generate 600
"""
from __future__ import annotations

import argparse
from pathlib import Path

import tensorflow as tf

AUTOTUNE = tf.data.AUTOTUNE
EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".gif")


def make_ds(class_dir: Path, img: int, batch: int):
    files = [str(p) for p in class_dir.rglob("*") if p.suffix.lower() in EXTS]
    print(f"[data] {len(files)} images in {class_dir.name}")

    def load(path):
        raw = tf.io.read_file(path)
        im = tf.io.decode_image(raw, channels=3, expand_animations=False)
        shape = tf.shape(im)
        s = tf.minimum(shape[0], shape[1])
        im = tf.image.resize_with_crop_or_pad(im, s, s)   # center-crop square
        im = tf.image.resize(im, [img, img])
        im = tf.image.random_flip_left_right(im)
        im = (tf.cast(im, tf.float32) - 127.5) / 127.5     # -> [-1, 1]
        im.set_shape([img, img, 3])
        return im

    return (tf.data.Dataset.from_tensor_slices(files)
            .shuffle(min(len(files), 4000))
            .map(load, num_parallel_calls=AUTOTUNE)
            .apply(tf.data.experimental.ignore_errors())
            .batch(batch, drop_remainder=True)
            .prefetch(AUTOTUNE)), len(files)


def build_generator(latent: int, img: int):
    start = img // 16            # 96 -> 6
    m = tf.keras.Sequential([
        tf.keras.layers.Input((latent,)),
        tf.keras.layers.Dense(start * start * 256, use_bias=False),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.ReLU(),
        tf.keras.layers.Reshape((start, start, 256)),
        tf.keras.layers.Conv2DTranspose(128, 4, 2, "same", use_bias=False),
        tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
        tf.keras.layers.Conv2DTranspose(64, 4, 2, "same", use_bias=False),
        tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
        tf.keras.layers.Conv2DTranspose(32, 4, 2, "same", use_bias=False),
        tf.keras.layers.BatchNormalization(), tf.keras.layers.ReLU(),
        tf.keras.layers.Conv2DTranspose(3, 4, 2, "same", activation="tanh"),
    ], name="generator")
    return m


def build_discriminator(img: int):
    return tf.keras.Sequential([
        tf.keras.layers.Input((img, img, 3)),
        tf.keras.layers.Conv2D(32, 4, 2, "same"),
        tf.keras.layers.LeakyReLU(0.2), tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Conv2D(64, 4, 2, "same"),
        tf.keras.layers.LeakyReLU(0.2), tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Conv2D(128, 4, 2, "same"),
        tf.keras.layers.LeakyReLU(0.2), tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Conv2D(256, 4, 2, "same"),
        tf.keras.layers.LeakyReLU(0.2), tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(1),
    ], name="discriminator")


def save_grid(imgs, path: Path, rows=8, cols=8):
    n = rows * cols
    imgs = tf.cast(tf.clip_by_value((imgs[:n] + 1.0) * 127.5, 0, 255), tf.uint8)
    h, w = imgs.shape[1], imgs.shape[2]
    g = tf.reshape(imgs, (rows, cols, h, w, 3))
    g = tf.transpose(g, (0, 2, 1, 3, 4))
    g = tf.reshape(g, (rows * h, cols * w, 3))
    tf.io.write_file(str(path), tf.io.encode_png(g))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--img-size", type=int, default=96)
    ap.add_argument("--latent", type=int, default=128)
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--n-generate", type=int, default=600)
    args = ap.parse_args()

    tf.keras.utils.set_random_seed(42)
    out = Path(args.out).expanduser(); out.mkdir(parents=True, exist_ok=True)
    class_dir = Path(args.class_dir).expanduser()

    ds, n_real = make_ds(class_dir, args.img_size, args.batch)
    gen = build_generator(args.latent, args.img_size)
    disc = build_discriminator(args.img_size)
    g_opt = tf.keras.optimizers.Adam(2e-4, 0.5)
    d_opt = tf.keras.optimizers.Adam(2e-4, 0.5)
    bce = tf.keras.losses.BinaryCrossentropy(from_logits=True)
    seed = tf.random.normal((64, args.latent))   # fixed seed for grid continuity

    @tf.function
    def step(real):
        bs = tf.shape(real)[0]
        z = tf.random.normal((bs, args.latent))
        with tf.GradientTape() as dt, tf.GradientTape() as gt:
            fake = gen(z, training=True)
            d_real = disc(real, training=True)
            d_fake = disc(fake, training=True)
            d_loss = (bce(tf.ones_like(d_real) * 0.9, d_real)
                      + bce(tf.zeros_like(d_fake), d_fake))
            g_loss = bce(tf.ones_like(d_fake), d_fake)
        d_opt.apply_gradients(zip(dt.gradient(d_loss, disc.trainable_variables),
                                  disc.trainable_variables))
        g_opt.apply_gradients(zip(gt.gradient(g_loss, gen.trainable_variables),
                                  gen.trainable_variables))
        return d_loss, g_loss

    print(f"==== DCGAN {class_dir.name}  img={args.img_size} epochs={args.epochs} ====")
    for e in range(1, args.epochs + 1):
        dl = gl = 0.0; nb = 0
        for real in ds:
            d, g = step(real); dl += float(d); gl += float(g); nb += 1
        print(f"epoch {e:3d}/{args.epochs}  d_loss={dl/nb:.3f}  g_loss={gl/nb:.3f}", flush=True)
        if e % 25 == 0 or e == args.epochs:
            save_grid(gen(seed, training=False), out / f"samples_epoch{e:03d}.png")

    # ---- final: save model + dump synthetic images for fold-in ----
    gen.save(out / "generator.keras")
    gdir = out / "generated"; gdir.mkdir(exist_ok=True)
    done = 0
    while done < args.n_generate:
        b = min(args.batch, args.n_generate - done)
        imgs = gen(tf.random.normal((b, args.latent)), training=False)
        imgs = tf.cast(tf.clip_by_value((imgs + 1.0) * 127.5, 0, 255), tf.uint8)
        for j in range(b):
            tf.io.write_file(str(gdir / f"gan_{done+j:05d}.png"),
                             tf.io.encode_png(imgs[j]))
        done += b
    print(f"[done] {n_real} real -> {args.n_generate} synthetic in {gdir}")


if __name__ == "__main__":
    main()
