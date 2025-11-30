import cv2
import numpy as np
import os

PHOTO_DIR = "photos"
VINTAGE_DIR = "photos_vintage"

if not os.path.exists(VINTAGE_DIR):
    os.makedirs(VINTAGE_DIR)

def apply_vintage_filter(filename):
    input_path = os.path.join(PHOTO_DIR, filename)
    
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_vintage{ext}"  # Append _vintage before extension
    output_path = os.path.join(VINTAGE_DIR, new_filename)

    image = cv2.imread(input_path)
    if image is None:
        print(f"Failed to load image: {input_path}")
        return False

    kernel = np.array([[0.272, 0.534, 0.131],
                       [0.349, 0.686, 0.168],
                       [0.393, 0.769, 0.189]])

    vintage_image = cv2.transform(image, kernel)
    vintage_image = np.clip(vintage_image, 0, 255).astype('uint8')

    cv2.imwrite(output_path, vintage_image)
    print(f"Saved vintage photo: {output_path}")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python vintage_filter.py <filename>")
        exit(1)
    apply_vintage_filter(sys.argv[1])
