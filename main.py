import Hobot.GPIO as GPIO
import time
import os
import signal
import sys
import threading
import capture_photos  # Your capture module
import bw_filter       # Black & white filter module
import vintage_filter  # Vintage filter module

BUTTON_CAPTURE = 13  # Button 1: capture photo (Pin 13, GPIO 27)
LED_CAPTURE = 31     # LED 1: capture indicator (Pin 31, GPIO 6)

BUTTON_FILTER = 29   # Button 2: filter button (Pin 29, GPIO 5)
LED_BW = 36          # LED 2: B&W filter indicator (Pin 36, GPIO 16)
LED_VINTAGE = 37     # LED 3: Vintage filter indicator (Pin 37, GPIO 26)

PHOTO_DIR = "photos"
PHOTO_BW_DIR = "photos_bw"
PHOTO_VINTAGE_DIR = "photos_vintage"

# Ensure directories exist
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)
if not os.path.exists(PHOTO_BW_DIR):
    os.makedirs(PHOTO_BW_DIR)
if not os.path.exists(PHOTO_VINTAGE_DIR):
    os.makedirs(PHOTO_VINTAGE_DIR)

exit_flag = False

def cleanup_and_exit():
    print("\nCleaning up...")
    capture_photos.close_camera()
    GPIO.cleanup()
    print("Cleanup complete. Exiting.")
    sys.exit(0)

def signal_handler(sig, frame):
    print(f"\nReceived signal {sig}.")
    cleanup_and_exit()

signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

def listen_for_exit():
    global exit_flag
    while True:
        user_input = input()
        if user_input.lower() == 'q':
            print("Exit command received.")
            exit_flag = True
            break

def main():
    global exit_flag
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(BUTTON_CAPTURE, GPIO.IN)
    GPIO.setup(BUTTON_FILTER, GPIO.IN)
    GPIO.setup(LED_CAPTURE, GPIO.OUT)
    GPIO.setup(LED_BW, GPIO.OUT)
    GPIO.setup(LED_VINTAGE, GPIO.OUT)

    GPIO.output(LED_CAPTURE, GPIO.LOW)
    GPIO.output(LED_BW, GPIO.LOW)
    GPIO.output(LED_VINTAGE, GPIO.LOW)

    print("Ready (press 'q' then Enter to quit)")

    listener_thread = threading.Thread(target=listen_for_exit, daemon=True)
    listener_thread.start()

    last_captured_filename = None
    button_capture_last_state = False
    button_filter_last_state = False
    filter_button_press_time = None

    try:
        while True:
            if exit_flag:
                print("Exiting main loop.")
                break

            # Capture button rising edge
            current_capture_state = GPIO.input(BUTTON_CAPTURE) == GPIO.HIGH
            if current_capture_state and not button_capture_last_state:
                print("Capture button pressed! Capturing...")
                success, filename = capture_photos.capture_photo()
                if success:
                    last_captured_filename = filename
                    print(f"Saved {filename}")
                    GPIO.output(LED_CAPTURE, GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(LED_CAPTURE, GPIO.LOW)
                else:
                    print("Capture failed!")
            button_capture_last_state = current_capture_state

            # Filter button press duration detection
            current_filter_state = GPIO.input(BUTTON_FILTER) == GPIO.HIGH

            if current_filter_state and not button_filter_last_state:
                # Button just pressed: start timing
                filter_button_press_time = time.time()

            if not current_filter_state and button_filter_last_state:
                # Button just released: calculate press duration
                duration = time.time() - filter_button_press_time if filter_button_press_time else 0

                if last_captured_filename is None:
                    print("No photo to apply filter!")
                else:
                    if 0 < duration <= 5:
                        print(f"Filter button pressed for {duration:.2f}s: Applying Black & White filter")
                        success = bw_filter.apply_bw_filter(os.path.basename(last_captured_filename))
                        if success:
                            GPIO.output(LED_BW, GPIO.HIGH)
                            time.sleep(1)
                            GPIO.output(LED_BW, GPIO.LOW)
                        else:
                            print("Failed to apply B&W filter.")
                    elif 5 < duration <= 6:
                        print(f"Filter button pressed for {duration:.2f}s: Applying Vintage filter")
                        success = vintage_filter.apply_vintage_filter(os.path.basename(last_captured_filename))
                        if success:
                            GPIO.output(LED_VINTAGE, GPIO.HIGH)
                            time.sleep(1)
                            GPIO.output(LED_VINTAGE, GPIO.LOW)
                        else:
                            print("Failed to apply vintage filter.")
                    else:
                        print(f"Filter button pressed for {duration:.2f}s: No filter applied")

                filter_button_press_time = None

            button_filter_last_state = current_filter_state

            time.sleep(0.05)

    except Exception as e:
        print(f"Error encountered: {e}")

    finally:
        cleanup_and_exit()

if __name__ == "__main__":
    main()
