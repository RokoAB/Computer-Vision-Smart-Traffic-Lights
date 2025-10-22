import cv2
import numpy as np
import time
import socket
import threading
import queue

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
        print("Failed to connect. Retrying in 2s...")
        time.sleep(2)

start_received = threading.Event()
instruction_queue = queue.Queue()

def receive_messages():
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
                elif ready_for_instructions:
                    instruction_queue.put(message)
        except Exception as e:
            print("Error receiving message:", e)
            break

recv_thread = threading.Thread(target=receive_messages, daemon=True)
recv_thread.start()

ready_for_instructions = False

while True:
    user_input = input("Type START to begin simulation: ").strip().upper()
    if user_input == "START":
        sock.sendall(b'START\n')
        ready_for_instructions = True
        print("Sent START to Raspberry Pi.")
        break

# Added a 7-second delay before traffic light cycle begins on this side 
print("Waiting 7 seconds before starting the first cycle...")
time.sleep(7) # needed for synchronization

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

first_cycle = True

while True:
    if first_cycle:
        print("First cycle: proceeding without Raspberry Pi instruction.")
        latest_instruction = "DEFAULT"
        first_cycle = False
    else:
        print("Waiting for Raspberry Pi instruction to begin next cycle...")
        print(f"Instructions in queue: {instruction_queue.qsize()}")
        try:
            latest_instruction = instruction_queue.get(timeout=5)
        except queue.Empty:
            print("No instruction received from Pi in time. Using DEFAULT.")
            latest_instruction = "DEFAULT"
        print(f"Starting new cycle with instruction: {latest_instruction}")

    green_duration = default_green_duration
    red_duration_effective = red_duration

    if latest_instruction == "NSEXTEND":
        red_duration_effective += additional_duration
        print(f"Extending RED light to {red_duration_effective} seconds.")
    elif latest_instruction == "EWEXTEND":
        green_duration += additional_duration
        print(f"Extending GREEN light to {green_duration} seconds.")
    elif latest_instruction == "DEFAULT":
        print(f"Using default durations. GREEN = {green_duration}, RED = {red_duration_effective}")
    else:
        print("Unknown instruction:", latest_instruction)

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
