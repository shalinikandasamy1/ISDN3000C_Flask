import os
import json
from collections import defaultdict
from flask import Flask, render_template, send_from_directory, redirect, url_for

app = Flask(__name__)

PHOTO_DIR = "photos"
LATEST_FILE = os.path.join(PHOTO_DIR, "latest.txt")

SESSION_FILE = "session_photos.json"
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
    if not os.path.exists(LATEST_FILE):
        return None
    with open(LATEST_FILE, "r") as f:
        name = f.read().strip()
    if not name:
        return None
    img_path = os.path.join(PHOTO_DIR, name)
    return name if os.path.exists(img_path) else None


# ---- session helpers ----

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


# SCREEN 1 – Welcome
@app.route("/welcome")
def welcome():
    return render_template("welcome.html")


# SCREEN 2 – Camera Live
@app.route("/camera")
def camera_live():
    return render_template("camera_live.html")


# SCREEN 3 – Preview
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
        max_reached=max_reached
    )


@app.route("/preview/accept")
def preview_accept():
    return redirect(url_for("gallery"))


@app.route("/preview/retake")
def preview_retake():
    return redirect(url_for("camera_live"))


# SCREEN 4 – Choose favourite photo
@app.route("/choose")
def choose_photo():
    session_photos = load_session_photos()
    card_urls = [
        (name, url_for("photos_file", filename=name))
        for name in session_photos
    ]
    return render_template("choose.html", card_urls=card_urls)


@app.route("/choose/<filename>")
def choose_confirm(filename):
    with open(LATEST_FILE, "w") as f:
        f.write(filename)
    return redirect(url_for("chosen"))


# SCREEN 5 – “You picked this photo” confirmation
@app.route("/chosen")
def chosen():
    latest = get_latest_photo()
    if latest:
        photo_url = url_for("photos_file", filename=latest)
    else:
        photo_url = None
    return render_template("chosen.html", photo_url=photo_url)


# SCREEN 6 – Filter game
@app.route("/filters")
def filter_game():
    latest = get_latest_photo()
    photo_url = url_for("photos_file", filename=latest) if latest else None
    return render_template("filters.html", photo_url=photo_url)

@app.route("/compare")
def compare():
    latest = get_latest_photo()          # chosen base photo
    if latest:
        original_url = url_for("photos_file", filename=latest)
        # assume your filters save to photos_bw / photos_vintage using same filename
        bw_url = url_for("static", filename=f"../photos_bw/{latest}")    # or vintage path
        # for now just show one filtered version; later you can switch per choice
        filtered_url = bw_url
    else:
        original_url = None
        filtered_url = None

    return render_template(
        "compare.html",
        original_url=original_url,
        filtered_url=filtered_url
    )


@app.route("/didyouknow")
def did_you_know():
    return render_template("didyouknow.html")

# Gallery
@app.route("/")
def gallery():
    groups = load_groups()
    return render_template("gallery.html", groups=groups)


# Serve photos
@app.route("/photos/<path:filename>")
def photos_file(filename):
    return send_from_directory(PHOTO_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
