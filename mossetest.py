#import os
#os.system('pip install opencv-contrib-python')

import cv2
import numpy as np
import time

# Load video file
video_path = "chase.mp4"  # Change this to your video file path
cap = cv2.VideoCapture(video_path)

tracker_mosse = None
tracker_tld = cv2.legacy.TrackerTLD_create()
bbox = None
tracking = False
lost_frames = 0
max_lost_frames = 30
prev_bbox = None
tracking_area_margin = 50  # Additional area to expand for re-tracking

def select_target(event, x, y, flags, param):
    global bbox, tracking, tracker_mosse, prev_bbox
    if event == cv2.EVENT_LBUTTONDOWN:
        bbox = cv2.selectROI("Select Object", frame, False)
        if bbox != (0, 0, 0, 0):  # Ensure a valid selection
            tracker_mosse = cv2.legacy.TrackerMOSSE_create()
            tracker_mosse.init(frame, bbox)
            tracker_tld = cv2.legacy.TrackerTLD_create()
            tracker_tld.init(frame, bbox)
            tracking = True
            prev_bbox = bbox  # Store the initial bounding box
        cv2.destroyWindow("Select Object")

cv2.namedWindow("MOSSE + TLD Tracker")
cv2.setMouseCallback("MOSSE + TLD Tracker", select_target)

fps = cap.get(cv2.CAP_PROP_FPS)
delay = int(1000 / fps) if fps > 0 else 30  # Calculate delay based on FPS

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Resize frame to 1/4 size
    height, width = frame.shape[:2]
    frame = cv2.resize(frame, (width // 2, height // 2))
    
    if tracking:
        # Try MOSSE Tracker
        if tracker_mosse is not None:
            success, bbox = tracker_mosse.update(frame)
            if success:
                x, y, w, h = [int(i) for i in bbox]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                prev_bbox = bbox  # Update the last known position
                lost_frames = 0  # Reset lost frame counter
            else:
                # If MOSSE fails, use TLD for recovery
                lost_frames += 1
                cv2.putText(frame, "MOSSE Tracking lost", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if lost_frames > max_lost_frames:
                    tracking = False  # Stop tracking after too many lost frames
                else:
                    if prev_bbox is not None:
                        tracker_tld = cv2.legacy.TrackerTLD_create()
                        tracker_tld.init(frame, prev_bbox)  # Reinitialize TLD with last known position
                    else:
                        # If no previous bbox, reset tracking
                        tracking = False

        # Try TLD Tracker if MOSSE fails
        if tracker_tld is not None and not tracker_mosse.update(frame)[0]:
            success, bbox = tracker_tld.update(frame)
            if success:
                x, y, w, h = [int(i) for i in bbox]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)  # TLD tracking in yellow
                prev_bbox = bbox  # Update the last known position
                lost_frames = 0  # Reset lost frame counter
            else:
                cv2.putText(frame, "TLD Tracking failed", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("MOSSE + TLD Tracker", frame)
    
    if cv2.waitKey(delay) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
