import cv2
import numpy as np
import time
import serial
import threading

pixel_change_threshold = 40
default_green_duration = 5
yellow_duration = 1
red_duration = 2
frame_check_count = 3
frame_capture_interval = 0.1

last_green_samples = []
last_red_samples = []
laptop_trigger = None
pi_trigger = None

try:
    laptop_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Adjust to your device path
    time.sleep(2)
    print("Connected to laptop via serial.")
    laptop_serial.write(b'START\n')
except Exception as e:
    print("Failed to connect to laptop serial:", e)
    exit()

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

while True:
    pi_trigger = False
    green_decision = "DEFAULT"

    print("\n Waiting for TRIGGER message from laptop...")
    laptop_trigger = None

    if pi_trigger:
        green_decision = "EXTEND"
    laptop_serial.write((green_decision + '\n').encode())
    print(f"Sent green light duration to laptop: {green_decision}")

    green_duration = default_green_duration if green_decision == "DEFAULT" else default_green_duration + 5

    print(f"\n GREEN ON ({green_duration} s)")
    green_start = time.time()
    last_green_samples.clear()

    while time.time() - green_start < green_duration:
        ret, frame = cap.read()
        if not ret:
            continue
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if green_duration - (time.time() - green_start) <= 0.5:
            if len(last_green_samples) < frame_check_count:
                last_green_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n YELLOW ON")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Traffic Feed", frame)

    print("\n RED ON")
    red_start = time.time()
    last_red_samples.clear()

    while time.time() - red_start < red_duration:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if red_duration - (time.time() - red_start) <= 0.5:
            if len(last_red_samples) < frame_check_count:
                last_red_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

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

    try:
        if laptop_serial.in_waiting:
            line = laptop_serial.readline().decode().strip()
            if line == "TRIGGER":
                laptop_trigger = True
                print("Laptop trigger received.")
    except Exception as e:
        print("Serial read failed:", e)


    if laptop_trigger is not None:
        msg = f"NS={int(pi_trigger)},EW={int(laptop_trigger)}\n"
        if arduino:
            try:
                arduino.write(msg.encode())
                print(f"Sent to Arduino: {msg.strip()}")
            except Exception as e:
                print("Failed to send to Arduino:", e)
        else:
            print("Arduino not connected.")
    else:
        print("Laptop trigger not received in time.")

    laptop_trigger = None
    pi_trigger = None

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
laptop_serial.close()
if arduino:
    arduino.close()
