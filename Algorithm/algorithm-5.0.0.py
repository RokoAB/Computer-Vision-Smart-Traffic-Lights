import cv2
import numpy as np
import time
import serial

pixel_change_threshold = 40
default_green_duration = 5
additional_duration = 5
yellow_duration = 2
red_duration = 4
frame_check_count = 3
frame_capture_interval = 0.1

try:
    ser = serial.Serial('COM3', 9600, timeout=2)  # Replace COM3 with actual port
    print("Serial connection established.")
except Exception as e:
    print("Failed to connect to serial port:", e)
    exit()

print("Waiting for START command from Raspberry Pi...")
while True:
    if ser.in_waiting:
        line = ser.readline().decode().strip()
        if line == "START":
            print("START received. Beginning traffic loop.")
            break

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

while True:
    green_duration = default_green_duration
    if ser.in_waiting:
        instruction = ser.readline().decode().strip()
        if instruction == "EXTEND":
            green_duration += additional_duration
            print("Green light extended to", green_duration, "seconds.")
        elif instruction == "DEFAULT":
            print("Default green light:", green_duration, "seconds.")
        else:
            print("Unknown instruction:", instruction)

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
                last_green_samples.append(frame_gray)
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            ser.close()
            exit()

    print("\n YELLOW ON")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Traffic Feed", frame)

    print("\n RED ON")
    red_start = time.time()
    last_red_samples = []

    while time.time() - red_start < red_duration:
        ret, frame = cap.read()
        if not ret:
            break

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if red_duration - (time.time() - red_start) <= 0.5:
            if len(last_red_samples) < frame_check_count:
                last_red_samples.append(frame_gray)
                time.sleep(frame_capture_interval)

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
            print("\n Movement detected!")
            break

    try:
        if movement_detected:
            ser.write(b'TRIGGER\n')
            print("Sent TRIGGER to Raspberry Pi.")
    except Exception as e:
        print("Failed to send trigger via serial:", e)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
