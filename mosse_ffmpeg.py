import cv2
import numpy as np
import subprocess
from flask import Flask, Response, render_template,request,jsonify

# RTSP 스트리밍 설정 (UDP 전송)
RTSP_URL = "rtsp://localhost:8554/mystream"
FFMPEG_CMD = [
    "ffmpeg", "-re", "-y", "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size", "640x480", "-i", "-",
    "-c:v", "libx264", 
    "-rtsp_transport", "udp", "-f", "rtsp", RTSP_URL
]

# FFmpeg 스트리밍 프로세스 시작
process = subprocess.Popen(FFMPEG_CMD, stdin=subprocess.PIPE)

# Flask 앱 생성
app = Flask(__name__)

# 비디오 캡처
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# MOSSE 트래커 생성
tracker = cv2.legacy.TrackerMOSSE_create()

# 첫 번째 프레임에서 객체 선택
ret, frame = cap.read()
if not ret:
    print("첫 번째 프레임을 읽을 수 없습니다.")
    cap.release()
    exit()

bbox = cv2.selectROI("Tracking", frame, False)
tracker.init(frame, bbox)
cv2.destroyWindow("Tracking")

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 트래커 업데이트
        success, bbox = tracker.update(frame)
        if success:
            x, y, w, h = map(int, bbox)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # FFmpeg로 전송
        process.stdin.write(frame.tobytes())
        
        # MJPEG 스트리밍을 위한 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
# 메인 페이지 라우트 - 스트리밍을 위한 HTML 렌더링
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/click', methods=['POST'])
def click_event():
    data = request.json  # {"x": 120, "y": 250}
    print(f"Mouse clicked at: {data}")  # 서버에 출력
    return jsonify({"status": "success", "received": data})
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

# 종료
cap.release()
process.stdin.close()
process.wait()
cv2.destroyAllWindows()
