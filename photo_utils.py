# photo_utils.py (in the same folder as app.py)
import os

PHOTO_DIR = "photos"

def get_latest_from_file():
    try:
        with open(os.path.join(PHOTO_DIR, "latest.txt")) as f:
            fname = f.read().strip()
        return os.path.join("photos", fname)
    except FileNotFoundError:
        return None
