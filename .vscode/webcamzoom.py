import cv2
import numpy as np
import os

# 초기 줌 비율 설정
zoom_factor = 100  # 기본 100 (최소 줌)
zoom_step = 10  # 줌 변경 단위
max_zoom = 260  # 최대 줌 값 (카메라에 따라 다름)
min_zoom = 0  # 최소 줌 값
# 4K 해상도 설정
frame_width = 3840
frame_height = 2160

# 카메라 열기 (디폴트 카메라: 0)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)


if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

def set_zoom(zoom_value):
    os.system(f'v4l2-ctl -d /dev/video0 -c zoom_absolute={zoom_value}')

def mouse_callback(event, x, y, flags, param):
    global zoom_factor
    if event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:
            zoom_factor = min(max_zoom, zoom_factor + zoom_step)
        else:
            zoom_factor = max(min_zoom, zoom_factor - zoom_step)
        set_zoom(zoom_factor)
        print(f"Zoom set to: {zoom_factor}")

cv2.namedWindow("USB Camera Stream")
cv2.setMouseCallback("USB Camera Stream", mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    cv2.imshow("USB Camera Stream", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('+'):
        zoom_factor = min(max_zoom, zoom_factor + zoom_step)
        set_zoom(zoom_factor)
        print(f"Zoom set to: {zoom_factor}")
    elif key == ord('-'):
        zoom_factor = max(min_zoom, zoom_factor - zoom_step)
        set_zoom(zoom_factor)
        print(f"Zoom set to: {zoom_factor}")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
