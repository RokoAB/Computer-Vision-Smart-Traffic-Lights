import cv2
import numpy as np
import time

pixel_change_threshold = 40  
default_green_duration = 5   
additional_duration = 2      
yellow_duration = 1          
red_duration = 2             
frame_check_count = 3       
frame_capture_interval = 0.1 # Seconds between sample frames

cap = cv2.VideoCapture(0)  

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

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

        # Take 3 samples in the last 0.5 sec of green
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

        # Take 3 samples in the last 0.5 sec of red
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
    object_count = 0

    for ref_frame, new_frame in zip(last_green_samples, last_red_samples):
        diff = cv2.absdiff(ref_frame, new_frame)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.dilate(thresh, kernel, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 4000:  
                object_count += 1
                print(f"Contour area: {area}")


                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
                cv2.putText(frame, f"Obj #{object_count}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


        changed_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size
        percentage_change = (changed_pixels / total_pixels) * 100

        print(f"Change: {percentage_change:.2f}%, Objects detected: {object_count}", end="\r")

        if percentage_change > pixel_change_threshold:
            print("\n Movement detected! Extending green light!")
            movement_detected = True
            green_duration += additional_duration
            break

        ref_resized = cv2.resize(ref_frame, (320, 240))
        new_resized = cv2.resize(new_frame, (320, 240))
        diff_resized = cv2.resize(thresh, (320, 240))
        cv2.imshow("Reference Frame (Green)", ref_resized)
        cv2.imshow("Comparison Frame (Red)", new_resized)
        cv2.imshow("Difference / Motion Mask", diff_resized)

        frame_resized = cv2.resize(frame, (320, 240))
        cv2.imshow("Detected Objects", frame_resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print(f"\n Total Moving Objects Detected in This Cycle: {object_count}")
cap.release()
cv2.destroyAllWindows()
