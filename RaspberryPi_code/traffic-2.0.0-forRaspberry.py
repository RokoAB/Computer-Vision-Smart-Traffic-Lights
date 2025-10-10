
import cv2
import numpy as np
import time
import serial
from picamera2 import Picamera2


try:
    arduino = serial.Serial('/dev/ttyACM0', 9600)  # Use /dev/ttyUSB0 or /dev/ttyACM0
    time.sleep(2)  # Wait for Arduino to initialize
    print("Connected to Arduino.")
except Exception as e:
    print("Could not connect to Arduino:", e)
    arduino = None


picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (640, 480)})
picam2.configure(camera_config)
picam2.start()

# === PARAMETERS ===
pixel_change_threshold = 40
default_green_duration = 5
additional_duration = 5
yellow_duration = 1
red_duration = 2
frame_check_count = 3
frame_capture_interval = 0.1

last_green_samples = []
last_red_samples = []


while True:
    green_duration = default_green_duration
    print("\nGREEN ON (Default:", green_duration, "s)")
    green_start = time.time()
    last_green_samples.clear()

    while time.time() - green_start < green_duration:
        frame = picam2.capture_array()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if green_duration - (time.time() - green_start) <= 0.5:
            if len(last_green_samples) < frame_check_count:
                last_green_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

    print("\n YELLOW ON (", yellow_duration, "s)")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        frame = picam2.capture_array()
        cv2.imshow("Traffic Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

    print("\n RED ON (", red_duration, "s)")
    red_start = time.time()
    last_red_samples.clear()

    while time.time() - red_start < red_duration:
        frame = picam2.capture_array()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if red_duration - (time.time() - red_start) <= 0.5:
            if len(last_red_samples) < frame_check_count:
                last_red_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

    print("\n Comparing frames...")
    movement_detected = False

    for ref_frame, new_frame in zip(last_green_samples, last_red_samples):
        diff = cv2.absdiff(ref_frame, new_frame)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        changed_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size
        percentage_change = (changed_pixels / total_pixels) * 100

        print(f"Change: {percentage_change:.2f}%", end="\r")

        if percentage_change > pixel_change_threshold:
            movement_detected = True
            print("\n Movement detected! Extending green light!")
            break

    if movement_detected and arduino:
        print(" Sending trigger to Arduino...")
        try:
            arduino.write(b'TRIGGER\n')
        except Exception as e:
            print(" Error writing to Arduino:", e)

    # Optional visual
    if movement_detected:
        cv2.imshow("Reference Frame", ref_frame)
        cv2.imshow("Comparison Frame", new_frame)
        cv2.imshow("Difference", thresh)
        cv2.waitKey(1000)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break

cv2.destroyAllWindows()


