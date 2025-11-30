import Hobot.GPIO as GPIO
import time
import capture_photos  # Ensure this provides capture_photo() -> (success, filename)

BUTTON_CAPTURE = 13  # GPIO 27 (BOARD pin 13)

def setup_gpio():
    GPIO.setmode(GPIO.BOARD)
    # Use internal pull-up resistor, button wired between GPIO and GND
    GPIO.setup(BUTTON_CAPTURE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("GPIO setup complete.")

if __name__ == "__main__":
    setup_gpio()

    print("Ready. Press the button to capture a photo.")

    try:
        while True:
            # Button pressed when input is LOW due to pull-up
            if GPIO.input(BUTTON_CAPTURE) == GPIO.LOW:
                print("Button pressed: capturing photo...")
                success, filename = capture_photos.capture_photo()
                if success:
                    print(f"Photo saved: {filename}")
                else:
                    print("Failed to capture photo.")
                time.sleep(1)  # Simple debounce delay

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Program interrupted by user.")

    finally:
        GPIO.cleanup()
        print("GPIO cleaned up. Exiting.")
