import cv2
import numpy as np
import time

video_path = "video1.mp4"  # Change this to your video file
pixel_change_threshold = 40  
default_green_duration = 5  
additional_duration = 2  # Extra seconds added if traffic is detected
yellow_duration = 1  
red_duration = 2  
frame_check_count = 3  # Number of frames to compare

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Cannot open video file.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
frame_time = 1.0 / fps  

while cap.isOpened():
    green_duration = default_green_duration  
    print("\n Green Light ON (Default:", green_duration, "seconds)")

    start_time = time.time()
    reference_frames = []  

    # Capture frames in the first 0.5 sec of green light
    for _ in range(frame_check_count):
        ret, frame = cap.read()
        if not ret:
            print("End")
            cap.release()
            exit()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        reference_frames.append(frame_gray)

        cv2.imshow("Live feed", frame)
        if cv2.waitKey(int(frame_time * 1000)) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    while time.time() - start_time < green_duration - 0.5:
        ret, frame = cap.read()
        if not ret:
            print("End")
            cap.release()
            exit()
        cv2.imshow("Live feed", frame)
        if cv2.waitKey(int(frame_time * 1000)) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n Comparison before end of light...")
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

            scale_percent = 80  
            width = int(ref_frame.shape[1] * scale_percent / 100)
            height = int(ref_frame.shape[0] * scale_percent / 100)
            dim = (width, height)

            ref_resized = cv2.resize(ref_frame, dim, interpolation=cv2.INTER_AREA)
            cur_resized = cv2.resize(frame_gray, dim, interpolation=cv2.INTER_AREA)
            diff_resized = cv2.resize(thresh, dim, interpolation=cv2.INTER_AREA)

            cv2.imshow("Reference frame", ref_resized)
            cv2.imshow("Curent frame", cur_resized)
            cv2.imshow("Difference", diff_resized)

            print(f"Pixel Change: {percentage_change:.2f}%", end="\r")

            if percentage_change > pixel_change_threshold:
                print("\n Trigger on. Extending the green light:", additional_duration, "seconds!")
                traffic_detected = True
                break  

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
