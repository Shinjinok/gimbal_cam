import cv2
import numpy as np
import subprocess
from flask import Flask, Response, render_template, request, jsonify

# Flask 앱 생성
app = Flask(__name__)

# 비디오 캡처
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# MOSSE 트래커 생성
tracker = cv2.legacy.TrackerMOSSE_create()
tracking_initialized = False  # 트래킹 초기화 여부
gx, gy = 0, 0  # 마우스 클릭 좌표 기본값


def setROI(frame):
    """ 마우스 클릭 좌표를 기준으로 트래커 초기화 """
    global tracker, tracking_initialized

    box = (gx-50, gy-50, 100, 100)
    tracker = cv2.legacy.TrackerMOSSE_create()  # 새로운 트래커 객체 생성
    tracker.init(frame, box)
    tracking_initialized = True  # 트래커가 초기화됨을 표시
    print(f"ROI 설정 완료: ({gx}, {gy})")


def generate_frames():
    global tracking_initialized

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 트래커 업데이트
        if tracking_initialized:
            success, bbox = tracker.update(frame)
            if success:
                x, y, w, h = map(int, bbox)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # MJPEG 스트리밍을 위한 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/click', methods=['POST'])
def click_event():
    global gx, gy, tracking_initialized

    data = request.json  # {"click_x": 120, "click_y": 250}
    gx = int(data["click_x"])
    gy = int(data["click_y"])
    
    ret, frame = cap.read()  # 현재 프레임 가져오기
    if ret:
        setROI(frame)  # ROI 설정
    
    print(f"Mouse clicked at: {gx}, {gy}")  # 서버 로그 출력
    return jsonify({"status": "success", "received": data})


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

cap.release()
cv2.destroyAllWindows()
