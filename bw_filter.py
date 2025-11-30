import cv2
import os

PHOTO_DIR = "photos"
BW_DIR = "photos_bw"

if not os.path.exists(BW_DIR):
    os.makedirs(BW_DIR)

def apply_bw_filter(filename):
    input_path = os.path.join(PHOTO_DIR, filename)
    
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_bw{ext}"  # Append _bw before extension
    output_path = os.path.join(BW_DIR, new_filename)

    image = cv2.imread(input_path)
    if image is None:
        print(f"Failed to load image: {input_path}")
        return False

    bw_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(output_path, bw_image)
    print(f"Saved black and white photo: {output_path}")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python bw_filter.py <filename>")
        exit(1)
    apply_bw_filter(sys.argv[1])
