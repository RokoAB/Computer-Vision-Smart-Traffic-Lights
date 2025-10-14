import cv2
import numpy as np
import time
import csv
import os

pixel_change_threshold = 10
default_green_duration = 4
additional_duration = 2
yellow_duration = 1
red_duration = 3
frame_check_count = 3
frame_capture_interval = 0.1

video_path = "video12.mp4"
cap = cv2.VideoCapture(video_path)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Error: Cannot open video file.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0 or np.isnan(fps):
    fps = 30.0
frame_time = 1.0 / fps

last_green_samples = []
last_red_samples = []

log_file = "traffic_feed.csv"
if not os.path.isfile(log_file):
    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Cycle", "Objects_No_Trigger", "Objects_With_Trigger", "Sizes"])

cycle_count = 0

while True:
    green_duration = default_green_duration
    print("\n GREEN ON (Default:", green_duration, "s)")
    green_start = time.time()
    last_green_samples.clear()

    while time.time() - green_start < green_duration:
        ret, frame = cap.read()
        if not ret:
            print("End of video reached.")
            cap.release()
            cv2.destroyAllWindows()
            exit()

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Live feed", frame)

        if green_duration - (time.time() - green_start) <= 0.5:
            if len(last_green_samples) < frame_check_count:
                last_green_samples.append(frame_gray)
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

        time.sleep(frame_time)

    print("\n YELLOW ON (", yellow_duration, "s)")
    yellow_start = time.time()
    while time.time() - yellow_start < yellow_duration:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Live feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()
        time.sleep(frame_time)

    print("\n RED ON (", red_duration, "s)")
    red_start = time.time()
    last_red_samples.clear()

    while time.time() - red_start < red_duration:
        ret, frame = cap.read()
        if not ret:
            break

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("Live feed", frame)

        if red_duration - (time.time() - red_start) <= 0.5:
            if len(last_red_samples) < frame_check_count:
                last_red_samples.append(frame_gray)
                time.sleep(frame_capture_interval)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()

        time.sleep(frame_time)

        print("\n Comparing last GREEN and RED samples...")
        movement_detected = False
        object_count = 0
        object_sizes = []

        for ref_frame, new_frame in zip(last_green_samples, last_red_samples):
            diff = cv2.absdiff(ref_frame, new_frame)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.dilate(thresh, kernel, iterations=2)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            frame_color = cv2.cvtColor(new_frame, cv2.COLOR_GRAY2BGR)

            temp_object_count = 0  
            temp_sizes = []       

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 4000:
                    temp_object_count += 1
                    temp_sizes.append(int(area))
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame_color, (x, y), (x + w, y + h), (255, 255, 255), 2)
                    cv2.putText(frame_color, f"Obj #{temp_object_count}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if temp_object_count > object_count:
                object_count = temp_object_count
                object_sizes = temp_sizes

            changed_pixels = np.sum(thresh > 0)
            total_pixels = thresh.size
            percentage_change = (changed_pixels / total_pixels) * 100

            print(f"Change: {percentage_change:.2f}%, Objects detected (this frame): {temp_object_count}", end="\r")

            cv2.imshow("Sampled frame (green)", cv2.resize(ref_frame, (320, 240)))
            cv2.imshow("Reference frame (red)", cv2.resize(new_frame, (320, 240)))
            cv2.imshow("Binary mask", cv2.resize(thresh, (320, 240)))
            cv2.imshow("Detected objects", cv2.resize(frame_color, (320, 240)))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                exit()

            time.sleep(frame_time)

            if percentage_change > pixel_change_threshold:
                print("\n Movement detected! Extending green light!")
                movement_detected = True
                green_duration += additional_duration
                break

    cycle_count += 1
    max_objects = max(1, len(object_sizes))

    if movement_detected:
        row = [cycle_count, 0, object_count] + object_sizes
    else:
        row = [cycle_count, object_count, 0] + object_sizes

    if not os.path.isfile(log_file):
        with open(log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            header = ["Cycle", "Objects_No_Trigger", "Objects_With_Trigger"]
            header += [f"Size{i+1}" for i in range(max_objects)]
            writer.writerow(header)

    with open(log_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)


    print(f"\n Total Objects in Cycle {cycle_count}: {object_count} | Trigger: {movement_detected}")
cap.release()
cv2.destroyAllWindows()
