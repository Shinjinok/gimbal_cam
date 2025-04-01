import cv2
import numpy as np
import time
import threading
import atexit
from flask import Flask, Response, render_template, request, jsonify

# Flask 앱 생성
app = Flask(__name__)

# 비디오 캡처 초기화
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# MOSSE 트래커 및 상태 변수
tracker = cv2.legacy.TrackerMOSSE_create()
tracking_initialized = False  # 트래킹 활성화 여부
gx, gy = None, None  # 클릭 좌표 (초기 None)
fail_count = 0  # 트래킹 실패 카운트
max_failures = 10  # 최대 실패 허용 횟수


def async_setROI():
    """비동기(스레드) 방식으로 ROI 설정"""
    global tracker, tracking_initialized, gx, gy

    while True:
        ret, frame = cap.read()
        if ret:
            break
        time.sleep(0.01)  # 프레임이 준비될 때까지 대기

    if gx is None or gy is None:
        print("ROI 설정 불가능: 좌표값이 설정되지 않음")
        return

    print(f"ROI 설정 중: ({gx}, {gy})")
    box = (gx - 50, gy - 50, 100, 100)
    tracker = cv2.legacy.TrackerMOSSE_create()
    tracker.init(frame, box)
    tracking_initialized = True
    print("ROI 설정 완료")


@app.route('/click', methods=['POST'])
def click_event():
    """클릭 이벤트 핸들러 - 좌표 저장 후 ROI 설정 비동기 실행"""
    global gx, gy, tracking_initialized

    data = request.json  # {"click_x": 120, "click_y": 250}
    gx, gy = int(data["click_x"]), int(data["click_y"])
    print(f"클릭 감지: {gx}, {gy}")

    # 기존 트래킹이 활성화되어 있으면 초기화
    tracking_initialized = False

    # 비동기(스레드)로 ROI 설정 실행
    threading.Thread(target=async_setROI, daemon=True).start()

    return jsonify({"status": "success", "received": data})


def generate_frames():
    """비디오 스트리밍 프레임 생성"""
    global tracking_initialized, fail_count

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다.")
            break

        # 프레임 크기 축소 (속도 최적화)
        frame = cv2.resize(frame, (320, 240))

        # 트래커 업데이트
        if tracking_initialized:
            success, bbox = tracker.update(frame)
            if success:
                fail_count = 0  # 추적 성공 시 카운트 초기화
                x, y, w, h = map(int, bbox)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                fail_count += 1
                if fail_count > max_failures:  # 일정 횟수 이상 실패 시 트래킹 종료
                    tracking_initialized = False
                    fail_count = 0
                    print("트래킹 실패: 종료")

        # MJPEG 스트리밍을 위한 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def cleanup():
    """Flask 종료 시 리소스 해제"""
    print("Flask 종료: 카메라 해제 및 창 닫기")
    cap.release()
    cv2.destroyAllWindows()


# 애플리케이션 종료 시 cleanup 실행
atexit.register(cleanup)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
