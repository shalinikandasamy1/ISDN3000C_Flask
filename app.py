import os
import json
import time
import threading
from collections import defaultdict
from flask import Flask, render_template, send_from_directory, redirect, url_for, request
import traceback

from email_helper import send_photobooth_email  # <-- you create this

# Create directories if missing
DIRS = ["photos", "photos_bw", "photos_vintage", "photos_style"]
for d in DIRS:
    os.makedirs(d, exist_ok=True)

# Safe import with fallback
try:
    import style_filter  # your style_filter.py
    STYLE_AVAILABLE = True
    print("✓ style_filter loaded successfully")
except ImportError as e:
    print(f"WARNING: style_filter.py not found: {e}")
    print("Style transfer will be disabled")
    style_filter = None
    STYLE_AVAILABLE = False

app = Flask(__name__)

PHOTO_DIR = "photos"
PHOTO_BW_DIR = "photos_bw"
PHOTO_VINTAGE_DIR = "photos_vintage"
STYLE_OUTPUT_DIR = "photos_style"
SESSION_FILE = "session_photos.json"
STYLE_STATUS_FILE = "style_latest.json"
MAX_RETAKES = 3

# ---------- helpers ----------

def load_groups():
    groups = defaultdict(list)
    if not os.path.exists(PHOTO_DIR):
        return groups
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
    if not os.path.exists(PHOTO_DIR):
        return None
    files = [f for f in os.listdir(PHOTO_DIR) if f.endswith(".jpg")]
    if not files:
        return None
    files.sort()
    return files[-1]

def get_latest_filtered_for(base_name):
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

def get_latest_style_file():
    if not os.path.exists(STYLE_OUTPUT_DIR):
        return None
    files = [f for f in os.listdir(STYLE_OUTPUT_DIR) if f.endswith(".jpg")]
    if not files:
        return None
    files.sort()
    return files[-1]

def load_session_photos():
    if not os.path.exists(SESSION_FILE):
        return []
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_session_photos(names):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(names, f)
    except Exception as e:
        print(f"Failed to save session: {e}")

def add_session_photo(filename):
    names = load_session_photos()
    names.append(filename)
    save_session_photos(names)
    return len(names)

# ---- style-transfer status helpers ----

def save_style_status(state, filename=None, phase=None):
    try:
        data = {"state": state, "filename": filename, "phase": phase, "ts": time.time()}
        with open(STYLE_STATUS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to save style status: {e}")

def load_style_status():
    if not os.path.exists(STYLE_STATUS_FILE):
        return {"state": "idle", "filename": None, "phase": None}
    try:
        with open(STYLE_STATUS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"state": "idle", "filename": None, "phase": None}

def start_style_job_for_latest():
    if not STYLE_AVAILABLE:
        return

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

# ---- ERROR HANDLER ----

@app.errorhandler(Exception)
def handle_error(e):
    print(f"SERVER ERROR: {str(e)}")
    print(traceback.format_exc())
    return "Internal server error. Check server logs.", 500

# ---------- FLOW ROUTES ----------

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/camera")
def camera_live():
    return render_template("camera_live.html")

@app.route("/trigger_capture")
def trigger_capture():
    latest = get_latest_photo()
    if latest:
        add_session_photo(latest)
    return redirect(url_for("buffer_game"))

@app.route("/buffer")
def buffer_game():
    return render_template("buffer.html")

@app.route("/preview")
def preview():
    latest = get_latest_photo()
    photo_url = url_for("photos_file", filename=latest) if latest else None

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

@app.route("/filters", methods=["GET", "POST"])
def filter_game():
    latest = get_latest_photo()
    photo_url = url_for("photos_file", filename=latest) if latest else None

    if request.method == "POST":
        return redirect(url_for("compare"))

    filtered_url = None
    if latest:
        kind, fname = get_latest_filtered_for(latest)
        if kind == "bw":
            filtered_url = url_for("photos_bw_file", filename=fname)
        elif kind == "vintage":
            filtered_url = url_for("photos_vintage_file", filename=fname)

    start_style_job_for_latest()
    status = load_style_status()
    styled_filename = status.get("filename")
    styled_url = None
    if styled_filename and status.get("state") == "done":
        styled_url = url_for("photos_style_file", filename=styled_filename)

    return render_template(
        "filters.html",
        photo_url=photo_url,
        filtered_url=filtered_url,
        styled_url=styled_url
    )

@app.route("/compare", methods=["GET", "POST"])
def compare():
    latest = get_latest_photo()
    photo_url = url_for("photos_file", filename=latest) if latest else None

    filtered_url = None
    if latest:
        kind, fname = get_latest_filtered_for(latest)
        if kind == "bw":
            filtered_url = url_for("photos_bw_file", filename=fname)
        elif kind == "vintage":
            filtered_url = url_for("photos_vintage_file", filename=fname)

    if request.method == "POST":
        return redirect(url_for("gallery"))

    return render_template(
        "compare.html",
        photo_url=photo_url,
        filtered_url=filtered_url
    )

@app.route("/didyouknow", methods=["GET", "POST"])
def did_you_know():
    if request.method == "POST":
        choice = request.form.get("choice")
        if choice == "yes":
            return redirect(url_for("finalize"))
        else:
            return redirect(url_for("qr_page"))
    return render_template("didyouknow.html")

@app.route("/finalize", methods=["GET", "POST"])
def finalize():
    if request.method == "POST":
        return redirect(url_for("qr_page"))

    base_name = get_latest_photo()
    if not base_name:
        return render_template("finalize.html", original_url=None, styled_url=None)

    original_url = url_for("photos_file", filename=base_name)

    styled_url = None
    style_file = get_latest_style_file()
    if style_file:
        styled_url = url_for("photos_style_file", filename=style_file)

    return render_template("finalize.html", original_url=original_url, styled_url=styled_url)

@app.route("/qr")
def qr_page():
    base_name = get_latest_photo()
    original_url = url_for("photos_file", filename=base_name) if base_name else None

    filtered_url = None
    if base_name:
        kind, fname = get_latest_filtered_for(base_name)
        if kind == "bw":
            filtered_url = url_for("photos_bw_file", filename=fname)
        elif kind == "vintage":
            filtered_url = url_for("photos_vintage_file", filename=fname)

    styled_url = None
    style_file = get_latest_style_file()
    if style_file:
        styled_url = url_for("photos_style_file", filename=style_file)

    return render_template(
        "qr.html",
        original_url=original_url,
        filtered_url=filtered_url,
        styled_url=styled_url
    )

# ---------- EMAIL SHARE ROUTE ----------

@app.route("/email_share", methods=["GET", "POST"])
def email_share():
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        base_name = get_latest_photo()
        attachments = []

        if base_name:
            attachments.append(os.path.join(PHOTO_DIR, base_name))

            kind, fname = get_latest_filtered_for(base_name)
            if kind == "bw":
                attachments.append(os.path.join(PHOTO_BW_DIR, fname))
            elif kind == "vintage":
                attachments.append(os.path.join(PHOTO_VINTAGE_DIR, fname))

        style_file = get_latest_style_file()
        if style_file:
            attachments.append(os.path.join(STYLE_OUTPUT_DIR, style_file))

        body = "Here are the three latest booth images, matching what you saw on screen."

        try:
            send_photobooth_email(
                to_email=email,
                subject="HKUST Photobooth images",
                body=body,
                attachments=attachments
            )
            sent_ok = True
        except Exception as e:
            print("Email send failed:", e)
            sent_ok = False

        return render_template("email_share.html", submitted=True, sent_ok=sent_ok)

    return render_template("email_share.html", submitted=False, sent_ok=None)

# ---------- gallery and static image routes ----------

@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    if request.method == "POST":
        return redirect(url_for("did_you_know"))
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

@app.route("/download/<kind>/<path:filename>")
def download_image(kind, filename):
    if kind == "original":
        img_url = url_for("photos_file", filename=filename, _external=True)
    elif kind == "bw":
        img_url = url_for("photos_bw_file", filename=filename, _external=True)
    elif kind == "vintage":
        img_url = url_for("photos_vintage_file", filename=filename, _external=True)
    elif kind == "style":
        img_url = url_for("photos_style_file", filename=filename, _external=True)
    else:
        return "Invalid link", 404

    return render_template("download.html", img_url=img_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8900, debug=True)
