import cv2
import numpy as np
import time

video_path = "video1.mp4"  # Change this to your video file
pixel_change_threshold = 10  
default_green_duration = 5  
additional_duration = 2  # Extra seconds added if traffic is detected
yellow_duration = 1  
red_duration = 5  
frame_check_count = 3  # Number of frames to compare

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Cannot open video file.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
frame_time = 1.0 / fps  
frames_to_check = int(0.5 * fps) 

while cap.isOpened():
    green_duration = default_green_duration 
    print("\n Green Light ON (Default:", green_duration, "seconds)")

    start_time = time.time()
    reference_frames = [] 

    # Capture frames in the first 0.5 sec of green light
    for _ in range(frame_check_count):
        ret, frame = cap.read()
        if not ret:
            print("End of video.")
            cap.release()
            exit()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        reference_frames.append(frame_gray)
        cv2.imshow("Traffic Feed", frame)
        if cv2.waitKey(int(frame_time * 1000)) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    while time.time() - start_time < green_duration - 0.5:
        ret, frame = cap.read()
        if not ret:
            print("End of video.")
            cap.release()
            exit()
        cv2.imshow("Traffic Feed", frame)
        if cv2.waitKey(int(frame_time * 1000)) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n Checking traffic presence before light change...")
    traffic_detected = False

    for _ in range(frame_check_count):
        ret, frame = cap.read()
        if not ret:
            print("End of video.")
            cap.release()
            exit()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for ref_frame in reference_frames:
            diff = cv2.absdiff(ref_frame, frame_gray)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

            changed_pixels = np.sum(thresh > 0)
            total_pixels = thresh.size
            percentage_change = (changed_pixels / total_pixels) * 100

            if percentage_change > pixel_change_threshold:
                print("\n Traffic Detected! Extending Green Light by", additional_duration, "seconds!")
                traffic_detected = True
                break 

        cv2.imshow("Traffic Feed", frame)
        if cv2.waitKey(int(frame_time * 1000)) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            exit()

        if traffic_detected:
            green_duration += additional_duration
            break  

    print("\n Yellow Light ON (", yellow_duration, "seconds)")
    time.sleep(yellow_duration)

    print("\n Red Light ON (", red_duration, "seconds)")
    time.sleep(red_duration)

cap.release()
cv2.destroyAllWindows()
