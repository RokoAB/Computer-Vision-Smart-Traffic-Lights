from flask import Flask, request, jsonify
import cv2
import numpy as np
import threading
import time
import sys

app = Flask(__name__)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    sys.exit(1)

pixel_change_threshold = 40
frame_check_count = 3
frame_capture_interval = 0.1

last_green_samples = []
last_red_samples = []

synced = False

@app.route('/from_pi', methods=['POST'])
def receive_from_pi():
    global synced, last_green_samples, last_red_samples

    data = request.get_json()
    print(f"Received from Pi: {data}")

    if not data or "type" not in data:
        return jsonify({"error": "Invalid data"}), 400

    if data["type"] == "sync" and data["value"] == "start":
        synced = True
        print("Sync started.")
        return jsonify({"status": "sync acknowledged"})

    elif data["type"] == "green":
        direction = data.get("direction", "")
        mode = data.get("mode", "")

        print(f"GREEN phase {direction} - Capturing reference frames...")
        last_green_samples.clear()
        for _ in range(frame_check_count):
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_green_samples.append(gray)
            time.sleep(frame_capture_interval)

        return jsonify({"status": "green captured"})

    elif data["type"] == "check_motion":
        print("RED phase - Capturing for motion detection...")
        last_red_samples.clear()
        for _ in range(frame_check_count):
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_red_samples.append(gray)
            time.sleep(frame_capture_interval)

        print("Comparing green and red samples...")
        movement_detected = False

        for ref, new in zip(last_green_samples, last_red_samples):
            diff = cv2.absdiff(ref, new)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            change_pct = (np.sum(thresh > 0) / thresh.size) * 100
            print(f"Change: {change_pct:.2f}%")

            if change_pct > pixel_change_threshold:
                movement_detected = True
                print("Movement Detected!")
                break

        try:
            import requests
            res = requests.post(
                "http://191.123.123.123:5001/trigger",  # Update with Pi's IP
                json={"source": "laptop", "trigger": movement_detected},
                timeout=2
            )
            print("Sent detection to Pi. Response:", res.json())
        except Exception as e:
            print("Failed to send detection to Pi:", e)

        return jsonify({"status": "motion checked", "movement": movement_detected})

    return jsonify({"status": "ignored"})


def run_flask():
    app.run(host="191.123.123.123", port=6000)


if __name__ == '__main__':
    try:
        threading.Thread(target=run_flask, daemon=True).start()
        print("Laptop Flask server running. Waiting for sync from Pi")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Exit")
    finally:
        cap.release()
        cv2.destroyAllWindows()
