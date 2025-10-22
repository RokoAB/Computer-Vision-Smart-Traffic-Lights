import cv2
import numpy as np
import time
import socket
import threading

pixel_change_threshold = 40
default_green_duration = 5
additional_duration = 5
yellow_duration = 2
red_duration = 7
frame_check_count = 3
frame_capture_interval = 0.1


SERVER_IP = '191.123.123.123'  # Replace with Pis IP address
PORT = 65432

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

while not connected:
    try:
        sock.connect((SERVER_IP, PORT))
        connected = True
        print("Connected to Raspberry Pi via TCP.")
    except Exception as e:
        print("Failed to connect...")
        time.sleep(2)

latest_instruction = None
start_received = threading.Event()

def receive_messages():
    global latest_instruction
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from Raspberry Pi.")
                break
            messages = data.decode().strip().split('\n')
            for message in messages:
                message = message.strip()
                if not message:
                    continue
                print(f"Received from Pi: {message}")
                if message == "START":
                    start_received.set()
                else:

                    if start_received.is_set():
                        latest_instruction = message
        except Exception as e:
            print("Error receiving message:", e)
            break

recv_thread = threading.Thread(target=receive_messages, daemon=True)
recv_thread.start()

while True:
    user_input = input("Type START to begin simulation: ").strip().upper()
    if user_input == "START":
        sock.sendall(b'START\n')
        print("Sent START to Raspberry Pi.")
        break
print("Starting local traffic loop from RED light.")


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

while True:
    green_duration = default_green_duration
    red_duration_effective = red_duration

    if latest_instruction == "NSEXTEND":
        green_duration += additional_duration
        print("Green light extended to", green_duration, "seconds.")
    elif latest_instruction == "EWEXTEND":
        red_duration_effective += additional_duration
        print("Red light extended to", red_duration_effective, "seconds.")
    elif latest_instruction == "DEFAULT":
        print("Default durations: GREEN =", green_duration, ", RED =", red_duration_effective)
    elif latest_instruction is not None:
        print("Unknown instruction:", latest_instruction)

    latest_instruction = None  # reset for next cycle

    print("\n RED ON")
    red_start = time.time()
    last_red_samples = []

    while time.time() - red_start < red_duration_effective:
        ret, frame = cap.read()
        if not ret:
            break

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Traffic Feed", frame)

        if red_duration_effective - (time.time() - red_start) <= 0.5:
            if len(last_red_samples) < frame_check_count:
                last_red_samples.append(frame_gray.copy())
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sock.close()
            exit()

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
            sock.close()
            exit()

    print("\n YELLOW ON")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Traffic Feed", frame)

    print("\n Comparing frames...")
    movement_detected = False
    for ref_frame, new_frame in zip(last_red_samples, last_green_samples):
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
            sock.sendall(b'TRIGGER\n')
            print("Sent TRIGGER to Raspberry Pi.")
        else:
            sock.sendall(b'NAN\n')
            print("Sent NAN to Raspberry Pi.")
    except Exception as e:
        print("Failed to send trigger with TCP:", e)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
sock.close()
