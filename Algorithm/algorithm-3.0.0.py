import cv2
import numpy as np
import time
import requests  

pixel_change_threshold = 40  
default_green_duration = 5   
additional_duration = 5      
yellow_duration = 1          
red_duration = 2             
frame_check_count = 3        
frame_capture_interval = 0.1 

cap = cv2.VideoCapture(0)  
if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0 or np.isnan(fps):
    fps = 30.0
frame_time = 1.0 / fps

last_green_samples = []
last_red_samples = []

while True:
    green_duration = default_green_duration
    print("\n GREEN ON (Default:", green_duration, "s)")
    green_start = time.time()
    last_green_samples.clear()

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
            exit()

    print("\n YELLOW ON (", yellow_duration, "s)")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Traffic Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n RED ON (", red_duration, "s)")
    red_start = time.time()
    last_red_samples.clear()

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

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n Comparing last GREEN and RED samples...")
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
            
            ref_resized = cv2.resize(ref_frame, (320, 240))
            new_resized = cv2.resize(new_frame, (320, 240))
            diff_resized = cv2.resize(thresh, (320, 240))
            cv2.imshow("Reference Frame (Green)", ref_resized)
            cv2.imshow("Comparison Frame (Red)", new_resized)
            cv2.imshow("Difference", diff_resized)
            break

        ref_resized = cv2.resize(ref_frame, (320, 240))
        new_resized = cv2.resize(new_frame, (320, 240))
        diff_resized = cv2.resize(thresh, (320, 240))
        cv2.imshow("Reference Frame (Green)", ref_resized)
        cv2.imshow("Comparison Frame (Red)", new_resized)
        cv2.imshow("Difference", diff_resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n Sending detection result to Raspberry Pi...")
    try:
        response = requests.post(
            "http://191.123.123.123:6000/trigger",  # Replace with actual IP
            json={
                "source": "laptop",
                "trigger": movement_detected
            },
            timeout=2
        )
        print(" Response from Pi:", response.json())
    except Exception as e:
        print(" Failed to contact Raspberry Pi:", e)

cap.release()
cv2.destroyAllWindows()
