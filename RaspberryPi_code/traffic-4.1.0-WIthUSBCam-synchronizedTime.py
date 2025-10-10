import cv2
import numpy as np
import time
import serial
import threading
from flask import Flask, request, jsonify
import requests


laptop_trigger = None      
pi_trigger = None          
current_phase = None       # Phase info received from Arduino
awaiting_trigger = False   # Whether we should send trigger data back
lock = threading.Lock()


try:
    arduino = serial.Serial('/dev/ttyACM0', 9600)
    time.sleep(2)
    print("Connected to Arduino.")
except Exception as e:
    print("Could not connect to Arduino:", e)
    arduino = None

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Could not open USB camera.")
    exit()

pixel_change_threshold = 40
frame_check_count = 3
frame_capture_interval = 0.1

last_green_samples = []
last_red_samples = []
LAPTOP_URL = "http://191.123.123.123:5432/from_pi"  # adjust port/path as needed

app = Flask(__name__)

@app.route('/trigger', methods=['POST'])  #POST
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

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()


def listen_to_arduino():
    global current_phase, awaiting_trigger, laptop_trigger, pi_trigger
    while True:
        if arduino and arduino.in_waiting:
            try:
                message = arduino.readline().decode().strip()


                if message == "SYNC_START":
                    print("SYNC START received from Arduino.")
                    try:
                        requests.post(LAPTOP_URL, json={"type": "sync", "value": "start"})
                    except Exception as e:
                        print(f"Could not notify laptop about SYNC_START: {e}")

                
                elif message.startswith("GREEN_NS:") or message.startswith("GREEN_EW:"):
                    print(f"Green phase info from Arduino: {message}")
                    parts = message.split(":")
                    if len(parts) == 2:
                        direction, mode = parts[0], parts[1]
                        try:
                            requests.post(LAPTOP_URL, json={"type": "green", "direction": direction, "mode": mode})
                        except Exception as e:
                            print(f"Could not notify laptop: {e}")


                elif message.startswith("PHASE:"):
                    with lock:
                        current_phase = message[6:].strip()
                        print(f"Arduino phase: {current_phase}")

                elif message == "SEND_TRIGGER":
                    print("Arduino requesting trigger info...")
                    with lock:
                        if laptop_trigger is not None and pi_trigger is not None:
                            msg = f"NS={int(pi_trigger)},EW={int(laptop_trigger)}\n"
                            arduino.write(msg.encode())
                            print(f"Trigger message sent: {msg.strip()}")
                            laptop_trigger = None
                            pi_trigger = None
                        else:
                            print("Waiting for both triggers to be available.")

            except Exception as e:
                print("Error reading from Arduino:", e)


# Start listening thread after serial setup
if arduino:
    arduino_thread = threading.Thread(target=listen_to_arduino, daemon=True)
    arduino_thread.start()


def detect_motion():
    global pi_trigger
    while True:
        with lock:
            phase = current_phase

        if phase == "GREEN_NS":
            print("\n GREEN NS Phase - Capturing reference frames...")
            last_green_samples.clear()
            for _ in range(frame_check_count):
                ret, frame = cap.read()
                if not ret:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                last_green_samples.append(gray)
                time.sleep(frame_capture_interval)

        elif phase == "RED_NS":
            print("\n RED NS Phase - Checking for motion...")
            last_red_samples.clear()
            for _ in range(frame_check_count):
                ret, frame = cap.read()
                if not ret:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                last_red_samples.append(gray)
                time.sleep(frame_capture_interval)

            detected = False
            for ref_frame, red_frame in zip(last_green_samples, last_red_samples):
                diff = cv2.absdiff(ref_frame, red_frame)
                _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
                change_pct = (np.sum(thresh > 0) / thresh.size) * 100
                print(f" Change detected: {change_pct:.2f}%")

                if change_pct > pixel_change_threshold:
                    detected = True
                    break

            with lock:
                pi_trigger = detected
                print(f" Pi trigger set: {pi_trigger}")


        time.sleep(0.1)

# Start motion detection loop
motion_thread = threading.Thread(target=detect_motion, daemon=True)
motion_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n Exiting...")
finally:
    cap.release()
    cv2.destroyAllWindows()
