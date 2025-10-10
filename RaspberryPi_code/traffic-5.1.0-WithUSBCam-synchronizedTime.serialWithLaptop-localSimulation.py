import cv2
import numpy as np
import time
import serial
import threading

pixel_change_threshold = 40
default_green_duration = 5
yellow_duration = 2
red_duration = 4
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

    green_decision = "DEFAULT"

    if laptop_trigger is not None:
        msg = f"NS={int(pi_trigger)},EW={int(laptop_trigger)}\n"
        if arduino:
            try:
                arduino.write(msg.encode())
                print(f"Sent to Arduino: {msg.strip()}")
            except Exception as e:
                print("Failed to send to Arduino:", e)


        try:
            time_limit = time.time() + 2  # wait max 2s for Arduino reply
            while time.time() < time_limit:
                if arduino.in_waiting:
                    decision_line = arduino.readline().decode().strip()
                    print(f" Received from Arduino: {decision_line}")

                    if "NS=" in decision_line:
                        green_decision = decision_line.split("=")[1].strip()
                    break
            else:
                print("No decision received from Arduino.")
        except Exception as e:
            print("Failed to read Arduino decision:", e)

   
        laptop_serial.write((green_decision + '\n').encode())
        print(f" Sent green light decision to laptop: {green_decision}")
    else:
        print("Laptop trigger not received in time.")


    green_duration = default_green_duration
    if green_decision == "EXTEND":
        green_duration += 5
        print(f"Local Pi GREEN extended to {green_duration} seconds.")
    else:
        print(f"Local Pi GREEN default: {green_duration} seconds.")

    print("\n GREEN ON")
    green_start = time.time()
    last_green_samples = []

    while time.time() - green_start < green_duration:
        ret, frame = cap.read()
        if not ret:
            break

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if green_duration - (time.time() - green_start) <= 0.5:
            if len(last_green_samples) < frame_check_count:
                last_green_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            laptop_serial.close()
            if arduino: arduino.close()
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
    last_red_samples = []

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

    laptop_trigger = None
    pi_trigger = None

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
laptop_serial.close()
if arduino:
    arduino.close()
