import cv2
import os
from datetime import datetime

PHOTO_DIR = "photos"

if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

cap = cv2.VideoCapture(2)  # Open default camera

if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

def get_next_photo_number(date_prefix):
    existing_files = [f for f in os.listdir(PHOTO_DIR) if f.startswith(date_prefix)]
    numbers = []
    for f in existing_files:
        try:
            # Extract the three-digit photo number after date_ prefix
            num = int(f[len(date_prefix) + 1 : len(date_prefix) + 4])
            numbers.append(num)
        except:
            pass
    return max(numbers) + 1 if numbers else 1

def capture_photo():
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        return False, ''

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    photo_num = get_next_photo_number(date_str)
    filename = f"{date_str}_{photo_num:03d}_{time_str}.jpg"
    filepath = os.path.join(PHOTO_DIR, filename)

    cv2.imwrite(filepath, frame)
    print(f"Saved photo: {filepath}")
    return True, filename

def close_camera():
    cap.release()
