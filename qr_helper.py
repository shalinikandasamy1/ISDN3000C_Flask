#!/usr/bin/env python3
"""
QR Code Generator for HKUST Art Lab Photos
Generates QR codes IN THE SAME FOLDER for ALL JPGs only. Runs forever, checks every 15s.
JPG → PNG (same name, different extension)
"""

import os
import time
import qrcode
from PIL import Image
from datetime import datetime

# Configuration
FOLDERS = ["photos", "photos_bw", "photos_style", "photos_vintage"]
CHECK_INTERVAL = 15  # seconds
BASE_URL = "http://192.168.1.23:8900"  # <-- change to your booth machine's IP

def generate_qr_for_image(image_path, base_url=BASE_URL):
    """Generate QR code in SAME folder for JPG only"""
    try:
        folder = os.path.dirname(image_path)
        filename = os.path.basename(image_path)

        # ONLY PROCESS JPG FILES
        if not filename.lower().endswith('.jpg'):
            return False

        name, _ = os.path.splitext(filename)  # Remove .jpg
        qr_filename = f"{name}.png"  # photo.jpg → photo.png
        qr_path = os.path.join(folder, qr_filename)

        # Skip if QR exists and is newer than JPG
        if os.path.exists(qr_path) and os.path.getmtime(qr_path) > os.path.getmtime(image_path):
            print(f"✓ QR up-to-date: {qr_filename}")
            return True

        # Map folder to download kind
        folder_map = {
            "photos":         "original",
            "photos_bw":      "bw",
            "photos_style":   "style",
            "photos_vintage": "vintage",
        }

        image_url = None
        folder_name = os.path.basename(folder)
        if folder_name in folder_map:
            kind = folder_map[folder_name]
            # QR points to download route
            image_url = f"{base_url}/download/{kind}/{filename}"

        if not image_url:
            print(f"⚠️ No URL mapping for {image_path}")
            return False

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4,
        )
        qr.add_data(image_url)
        qr.make(fit=True)

        # Dark gradient QR matching your UI
        qr_img = qr.make_image(
            fill_color="#1a1a2e",
            back_color="#16213e"
        )

        # Save QR IN SAME FOLDER as JPG
        qr_img.save(qr_path)
        print(f"✨ QR created: {folder}/{qr_filename} -> {image_url}")
        return True

    except Exception as e:
        print(f"❌ QR FAILED {image_path}: {e}")
        return False

def scan_all_folders():
    """Scan all folders - ONLY JPGs get QRs"""
    total_checked = 0
    qrs_created = 0

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Scanning JPGs only...")

    for folder in FOLDERS:
        if not os.path.exists(folder):
            print(f"⚠️ Folder missing: {folder}")
            continue

        # ONLY JPG FILES
        jpg_files = [f for f in os.listdir(folder) if f.lower().endswith('.jpg')]

        print(f"📁 {folder}: {len(jpg_files)} JPGs")
        total_checked += len(jpg_files)

        for jpg_file in jpg_files:
            image_path = os.path.join(folder, jpg_file)
            if generate_qr_for_image(image_path):
                qrs_created += 1

    print(f"✅ Scan complete: {total_checked} JPGs checked, {qrs_created} new QRs")
    return total_checked, qrs_created

def main():
    """Main monitoring loop - JPGs ONLY"""
    print("🚀 HKUST Art Lab QR Code Keeper (JPG → PNG)")
    print(f"📂 Watching JPGs in: {', '.join(FOLDERS)}")
    print("💾 JPG.jpg → JPG.png (same folder)")
    print(f"⏱️ Checking every {CHECK_INTERVAL}s")
    print("-" * 70)

    consecutive_no_changes = 0
    while True:
        try:
            total_jpgs, new_qrs = scan_all_folders()

            if new_qrs == 0:
                consecutive_no_changes += 1
                status = "😴 All JPGs have QRs" if consecutive_no_changes > 1 else "✅ No new JPGs"
            else:
                consecutive_no_changes = 0
                status = f"✨ Created {new_qrs} new QRs"

            print(f"⏰ Next scan in {CHECK_INTERVAL}s... {status}")
            print("-" * 70)

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n👋 QR Keeper stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
