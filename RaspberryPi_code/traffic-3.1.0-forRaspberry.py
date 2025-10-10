# pip install flask FIRST INSTALL FLASK

import cv2
import numpy as np
import time
import serial
import threading
from flask import Flask, request, jsonify
from picamera2 import Picamera2

laptop_trigger = None  # Value sent from laptop
pi_trigger = None      # Locally detected value
lock = threading.Lock()

try:
    arduino = serial.Serial('/dev/ttyACM0', 9600)
    time.sleep(2)
    print("Connected to Arduino.")
except Exception as e:
    print("Could not connect to Arduino:", e)
    arduino = None


picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (640, 480)})
picam2.configure(camera_config)
picam2.start()

pixel_change_threshold = 40
default_green_duration = 5
yellow_duration = 1
red_duration = 2
frame_check_count = 3
frame_capture_interval = 0.1

last_green_samples = []
last_red_samples = []

app = Flask(__name__)

@app.route('/trigger', methods=['POST'])
def receive_trigger():
    global laptop_trigger
    data = request.get_json()
    if data and "trigger" in data and data.get("source") == "laptop":
        with lock:
            laptop_trigger = bool(data["trigger"])
            print(f"Laptop trigger received: {laptop_trigger}")
        return jsonify({"status": "received"}), 200
    return jsonify({"error": "Invalid data"}), 400

def run_server():
    app.run(host='0.0.0.0', port=5000)

# Start Flask server in background thread
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

while True:

    pi_trigger = False
    green_start = time.time()
    last_green_samples.clear()

    print("\n GREEN ON")
    while time.time() - green_start < default_green_duration:
        frame = picam2.capture_array()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if default_green_duration - (time.time() - green_start) <= 0.5:
            if len(last_green_samples) < frame_check_count:
                last_green_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            exit()

    print("\n YELLOW ON")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        frame = picam2.capture_array()
        cv2.imshow("Traffic Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            exit()

    print("\n RED ON")
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
            exit()

    print("\n Analyzing frames...")
    for ref_frame, new_frame in zip(last_green_samples, last_red_samples):
        diff = cv2.absdiff(ref_frame, new_frame)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        changed_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size
        percentage_change = (changed_pixels / total_pixels) * 100
        print(f"Change: {percentage_change:.2f}%", end="\r")

        if percentage_change > pixel_change_threshold:
            pi_trigger = True
            print("\n Pi: Movement detected!")
            break

    with lock:
        if laptop_trigger is not None:
            print(f"\n Preparing to send: Laptop={laptop_trigger}, Pi={pi_trigger}")
            if arduino:
                try:
                    msg = f"NS={int(pi_trigger)},EW={int(laptop_trigger)}\n"
                    arduino.write(msg.encode())
                    print(f" Trigger message sent to Arduino: {msg.strip()}")
                except Exception as e:
                    print(" Error writing to Arduino:", e)
            else:
                print("Arduino not connected.")
            # Reset for next cycle
            laptop_trigger = None
            pi_trigger = None
        else:
            print("Waiting for laptop trigger...")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break

cv2.destroyAllWindows()


