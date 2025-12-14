import os
import json
from datetime import datetime
import cv2

PHOTO_DIR = "photos"

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def analyze_photo(filename):
    img_path = os.path.join(PHOTO_DIR, filename)
    if not os.path.exists(img_path):
        print(f"AI: Image not found: {img_path}")
        return False

    img = cv2.imread(img_path)
    if img is None:
        print(f"AI: Failed to load image {img_path}")
        return False

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    num_faces = len(faces)
    has_face = num_faces > 0

    # Temporary simple rule – replace with real ID logic later
    if num_faces == 0:
        person_label = "unknown"
    elif num_faces == 1:
        person_label = "person 1"
    else:
        person_label = "group"

    base, _ = os.path.splitext(filename)
    out_path = os.path.join(PHOTO_DIR, base + ".json")

    metadata = {
        "filename": filename,
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "num_faces": num_faces,
        "has_face": has_face,
        "person": person_label
    }

    with open(out_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"AI: Saved analysis to {out_path} (faces: {num_faces}, person={person_label})")
    return True
