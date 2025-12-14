import os
import json
from collections import defaultdict
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

PHOTO_DIR = "photos"

def load_groups():
    groups = defaultdict(list)

    # Look at all JSON files in photos/
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

@app.route("/")
def gallery():
    groups = load_groups()
    return render_template("gallery.html", groups=groups)

# Serve images directly from photos/ (same as when it “worked before”)
@app.route("/photos/<path:filename>")
def photos_file(filename):
    return send_from_directory(PHOTO_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
