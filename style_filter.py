# style_filter.py
import os
import tensorflow as tf
from tensorflow.keras.applications import vgg19
import numpy as np
from PIL import Image

# where your style image + outputs live
STYLE_IMAGE_PATH = "static/img/hkust_style.png"   # put any style jpg here
STYLE_OUTPUT_DIR = "photos_style"

# ------------ hyperparameters ------------
STYLE_LAYERS = [
    "block1_conv1",
    "block2_conv1",
    "block3_conv1",
    "block4_conv1",
    "block5_conv1",
]
STYLE_LAYER_WEIGHTS = [3.0, 2.0, 1.0, 0.5, 0.3]
CONTENT_LAYER = "block5_conv2"

STYLE_WEIGHT   = 5e2
CONTENT_WEIGHT = 1e1
TV_WEIGHT      = 4.0
NUM_STEPS      = 200
LEARNING_RATE  = 0.02
MAX_DIM        = 512

# ------------ utilities ------------

def load_img(path_to_img, max_dim=MAX_DIM):
    img = tf.io.read_file(path_to_img)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = tf.reduce_max(shape)
    scale = max_dim / long_dim
    new_shape = tf.cast(shape * scale, tf.int32)
    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img

def tensor_to_image(tensor):
    tensor = tensor * 255.0
    tensor = np.array(tensor, dtype=np.uint8)
    if tensor.ndim > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return Image.fromarray(tensor)

def gram_matrix(tensor):
    result = tf.linalg.einsum("bijc,bijd->bcd", tensor, tensor)
    h = tf.cast(tf.shape(tensor)[1], tf.float32)
    w = tf.cast(tf.shape(tensor)[2], tf.float32)
    return result / (h * w)

def get_vgg_model():
    vgg = vgg19.VGG19(weights="imagenet", include_top=False)
    vgg.trainable = False
    outputs = [vgg.get_layer(name).output for name in STYLE_LAYERS + [CONTENT_LAYER]]
    return tf.keras.Model(vgg.input, outputs)

# ------------ core logic------------

def run_style_transfer(content_path, style_path, output_path):
    content_image = load_img(content_path)
    style_image = load_img(style_path)

    vgg_model = get_vgg_model()

    def vgg_preprocess(x):
        return vgg19.preprocess_input(x * 255.0)

    style_targets = vgg_model(vgg_preprocess(style_image))
    content_targets = vgg_model(vgg_preprocess(content_image))

    num_style_layers = len(STYLE_LAYERS)
    style_target_features = [gram_matrix(t) for t in style_targets[:num_style_layers]]
    content_target_features = content_targets[num_style_layers:]

    @tf.function
    def compute_loss_and_grads(img_var):
        with tf.GradientTape() as tape:
            outputs = vgg_model(vgg_preprocess(img_var))
            style_outputs = outputs[:num_style_layers]
            content_outputs = outputs[num_style_layers:]

            style_loss = 0.0
            for w, target_gram, out in zip(
                STYLE_LAYER_WEIGHTS, style_target_features, style_outputs
            ):
                gram_out = gram_matrix(out)
                style_loss += w * tf.reduce_mean(tf.square(gram_out - target_gram))
            style_loss *= STYLE_WEIGHT / sum(STYLE_LAYER_WEIGHTS)

            content_loss = 0.0
            for t_c, o_c in zip(content_target_features, content_outputs):
                content_loss += tf.reduce_mean(tf.square(o_c - t_c))
            content_loss *= CONTENT_WEIGHT

            tv_loss = tf.image.total_variation(img_var)
            tv_loss = TV_WEIGHT * tf.reduce_mean(tv_loss)

            total_loss = style_loss + content_loss + tv_loss

        grads = tape.gradient(total_loss, img_var)
        return grads, total_loss

    stylized_var = tf.Variable(content_image, dtype=tf.float32)
    optimizer = tf.optimizers.Adam(learning_rate=LEARNING_RATE)

    best_img = None
    best_loss = float("inf")

    for step in range(1, NUM_STEPS + 1):
        grads, total_loss = compute_loss_and_grads(stylized_var)
        optimizer.apply_gradients([(grads, stylized_var)])
        stylized_var.assign(tf.clip_by_value(stylized_var, 0.0, 1.0))

        if total_loss < best_loss:
            best_loss = total_loss
            best_img = stylized_var.numpy()

    final_pil = tensor_to_image(best_img)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_pil.save(output_path)
    return output_path

# helper: run on latest photo with fixed style
def run_style_on_latest(content_path, output_basename):
    os.makedirs(STYLE_OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(STYLE_OUTPUT_DIR, output_basename)
    return run_style_transfer(content_path, STYLE_IMAGE_PATH, out_path)
