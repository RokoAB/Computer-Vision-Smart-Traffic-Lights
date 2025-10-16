import cv2
import numpy as np
import time
from flask import Flask, request, jsonify
import threading

pixel_change_threshold = 40
frame_check_count = 3
frame_capture_interval = 0.1

app = Flask(__name__)
latest_trigger = {"trigger": False}

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print(" Error: Cannot open webcam.")
    exit()

def monitor_camera():
    global latest_trigger
    print(" Camera monitoring started...")
    last_green_samples = []
    last_red_samples = []

    while True:
        last_green_samples.clear()
        for _ in range(frame_check_count):
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_green_samples.append(gray)
            time.sleep(frame_capture_interval)

        time.sleep(2)  

        last_red_samples.clear()
        for _ in range(frame_check_count):
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_red_samples.append(gray)
            time.sleep(frame_capture_interval)

        movement_detected = False
        for ref_frame, new_frame in zip(last_green_samples, last_red_samples):
            diff = cv2.absdiff(ref_frame, new_frame)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

            changed_pixels = np.sum(thresh > 0)
            total_pixels = thresh.size
            percent_change = (changed_pixels / total_pixels) * 100

            if percent_change > pixel_change_threshold:
                movement_detected = True
                break

        latest_trigger["trigger"] = movement_detected
        print(f" Movement Detected: {movement_detected}")
        time.sleep(1)  # Cooldown to prevent CPU overload

@app.route("/trigger", methods=["GET"])
def send_trigger_status():
    return jsonify({
        "source": "laptop",
        "trigger": latest_trigger["trigger"]
    })

if __name__ == "__main__":
    # Start movement detection in the background
    threading.Thread(target=monitor_camera, daemon=True).start()

    # Start Flask server for Pi to query trigger
    print(" Starting Laptop Flask server on port 5001...")
    app.run(host="http://123.456.67.89", port=5001)
