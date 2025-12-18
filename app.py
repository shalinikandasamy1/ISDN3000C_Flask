import os
import json
import time
import threading
from collections import defaultdict
from flask import Flask, render_template, send_from_directory, redirect, url_for

import style_filter  # your style_filter.py

app = Flask(__name__)

PHOTO_DIR = "photos"
PHOTO_BW_DIR = "photos_bw"
PHOTO_VINTAGE_DIR = "photos_vintage"
STYLE_OUTPUT_DIR = "photos_style"

SESSION_FILE = "session_photos.json"
STYLE_STATUS_FILE = "style_latest.json"
MAX_RETAKES = 3


def load_groups():
    groups = defaultdict(list)
    for fname in os.listdir(PHOTO_DIR):
        if not fname.endswith(".json"):
            continue
        json_path = os.path.join(PHOTO_DIR, fname)
        try:
            with open(json_path, "r") as f:
                meta = json.load(f)
        except Exception as e:
            print("Failed to read", json_path, e)
            continue
        img_name = meta.get("filename")
        person = meta.get("person", "unknown")
        if img_name:
            groups[person].append(img_name)
    return groups


def get_latest_photo():
    files = [f for f in os.listdir(PHOTO_DIR) if f.endswith(".jpg")]
    if not files:
        return None
    files.sort()
    return files[-1]


def get_latest_photos(n=3):
    files = [f for f in os.listdir(PHOTO_DIR) if f.endswith(".jpg")]
    if not files:
        return []
    files.sort()
    latest = files[-n:]
    return list(reversed(latest))


def get_latest_filtered_for(base_name):
    """
    For original like 20000101_028_122051.jpg, look for:
      photos_bw/20000101_028_122051_bw.jpg
      photos_vintage/20000101_028_122051_vintage.jpg
    and return (kind, filename) for the newer one.
    kind is "bw" or "vintage".
    """
    root, _ = os.path.splitext(base_name)
    bw_name = f"{root}_bw.jpg"
    v_name = f"{root}_vintage.jpg"

    candidates = []

    bw_path = os.path.join(PHOTO_BW_DIR, bw_name)
    if os.path.exists(bw_path):
        candidates.append((os.path.getmtime(bw_path), "bw", bw_name))

    v_path = os.path.join(PHOTO_VINTAGE_DIR, v_name)
    if os.path.exists(v_path):
        candidates.append((os.path.getmtime(v_path), "vintage", v_name))

    if not candidates:
        return None, None

    candidates.sort(key=lambda t: t[0])
    _, kind, fname = candidates[-1]
    return kind, fname


def load_session_photos():
    if not os.path.exists(SESSION_FILE):
        return []
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_session_photos(names):
    with open(SESSION_FILE, "w") as f:
        json.dump(names, f)


def add_session_photo(filename):
    names = load_session_photos()
    names.append(filename)
    save_session_photos(names)
    return len(names)


# ---- style-transfer status helpers (backend-only) ----

def save_style_status(state, filename=None, phase=None):
    data = {"state": state, "filename": filename, "phase": phase, "ts": time.time()}
    with open(STYLE_STATUS_FILE, "w") as f:
        json.dump(data, f)


def load_style_status():
    if not os.path.exists(STYLE_STATUS_FILE):
        return {"state": "idle", "filename": None, "phase": None}
    try:
        with open(STYLE_STATUS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"state": "idle", "filename": None, "phase": None}


def start_style_job_for_latest():
    base_name = get_latest_photo()
    if not base_name:
        return

    content_path = os.path.join(PHOTO_DIR, base_name)
    out_name = os.path.splitext(base_name)[0] + "_style.jpg"

    def job():
        save_style_status("running", out_name, phase="loading")
        try:
            style_filter.run_style_on_latest(content_path, out_name)
            save_style_status("done", out_name, phase="finished")
        except Exception as e:
            print("Style job failed:", e)
            save_style_status("error", out_name, phase="error")

    threading.Thread(target=job, daemon=True).start()


# ---- routes ----

@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/camera")
def camera_live():
    return render_template("camera_live.html")


@app.route("/trigger_capture")
def trigger_capture():
    return redirect(url_for("buffer_game"))


@app.route("/buffer")
def buffer_game():
    return render_template("buffer.html")


@app.route("/preview")
def preview():
    latest = get_latest_photo()
    if latest:
        photo_url = url_for("photos_file", filename=latest)
    else:
        photo_url = None

    session_photos = load_session_photos()
    retake_count = len(session_photos)
    max_reached = retake_count >= MAX_RETAKES

    return render_template(
        "preview.html",
        photo_url=photo_url,
        retake_count=retake_count,
        max_reached=max_reached,
        max_retakes=MAX_RETAKES
    )


@app.route("/preview/accept")
def preview_accept():
    return redirect(url_for("filter_game"))


@app.route("/preview/retake")
def preview_retake():
    return redirect(url_for("camera_live"))


@app.route("/filters")
def filter_game():
    latest = get_latest_photo()
    photo_url = url_for("photos_file", filename=latest) if latest else None

    # kick off style transfer in background for the latest photo
    start_style_job_for_latest()

    return render_template("filters.html", photo_url=photo_url)


@app.route("/compare")
def compare():
    base_name = get_latest_photo()
    if not base_name:
        return render_template(
            "compare.html",
            original_url=None,
            filtered_url=None
        )

    original_url = url_for("photos_file", filename=base_name)

    kind, fname = get_latest_filtered_for(base_name)
    if kind == "bw":
        filtered_url = url_for("photos_bw_file", filename=fname)
    elif kind == "vintage":
        filtered_url = url_for("photos_vintage_file", filename=fname)
    else:
        filtered_url = None

    return render_template(
        "compare.html",
        original_url=original_url,
        filtered_url=filtered_url
    )


@app.route("/didyouknow")
def did_you_know():
    return render_template("didyouknow.html")


# waiting page for style result
@app.route("/art_wait")
def art_wait():
    status = load_style_status()
    ready = status.get("state") == "done"
    return render_template("art_wait.html", ready=ready)


@app.route("/art_wait/continue")
def art_wait_continue():
    status = load_style_status()
    if status.get("state") != "done":
        return redirect(url_for("art_wait"))
    return redirect(url_for("art_result"))


@app.route("/art_result")
def art_result():
    # always show the latest stylized file in photos_style
    style_files = [
        f for f in os.listdir(STYLE_OUTPUT_DIR)
        if f.endswith(".jpg")
    ]
    if not style_files:
        return render_template("art_result.html", style_url=None)

    style_files.sort()
    latest_style = style_files[-1]
    style_url = url_for("photos_style_file", filename=latest_style)
    return render_template("art_result.html", style_url=style_url)


@app.route("/gallery")
def gallery():
    groups = load_groups()
    return render_template("gallery.html", groups=groups)


@app.route("/photos/<path:filename>")
def photos_file(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/photos_bw/<path:filename>")
def photos_bw_file(filename):
    return send_from_directory(PHOTO_BW_DIR, filename)


@app.route("/photos_vintage/<path:filename>")
def photos_vintage_file(filename):
    return send_from_directory(PHOTO_VINTAGE_DIR, filename)


@app.route("/photos_style/<path:filename>")
def photos_style_file(filename):
    return send_from_directory(STYLE_OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8900)
