import cv2
import numpy as np
import time

video_path = "video1.mp4"  # Change this to your video file
pixel_change_threshold = 10  
default_green_duration = 2  
additional_duration = 2  # Extra seconds added if traffic is detected
yellow_duration = 1  
red_duration = 5  

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Cannot open video file.")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
frame_time = 1.0 / fps  

ret, frame1 = cap.read()
if not ret:
    print("Error: Cannot read video file.")
    exit()
frame1_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

while cap.isOpened():
    green_duration = default_green_duration  
    print("\n Green Light ON (Default:", green_duration, "seconds)")

    start_time = time.time()
    while time.time() - start_time < green_duration:
        
        ret, frame2 = cap.read()
        if not ret:
            print("End of video.")
            cap.release()
            exit()

        frame2_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)


        diff = cv2.absdiff(frame1_gray, frame2_gray)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        changed_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size
        percentage_change = (changed_pixels / total_pixels) * 100

        print(f"Pixel Change: {percentage_change:.2f}%", end="\r")

        if percentage_change > pixel_change_threshold:
            print("\n Traffic Detected! Extending Green Light by", additional_duration, "seconds!")
            green_duration += additional_duration
            start_time = time.time()  

        frame1_gray = frame2_gray  

        cv2.imshow("Traffic Feed", frame2)
        cv2.imshow("Frame Difference", thresh)
        
        if cv2.waitKey(int(frame_time * 1000)) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            exit()

    print("\n Yellow Light ON (", yellow_duration, "seconds)")
    time.sleep(yellow_duration)

    print("\n Red Light ON (", red_duration, "seconds)")
    time.sleep(red_duration)

cap.release()
cv2.destroyAllWindows()
