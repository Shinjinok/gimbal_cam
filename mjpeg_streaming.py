from flask import Flask, Response
import cv2
import threading

# 비디오 파일 경로
#video_path = "chase.mp4"  # 변경 필요
app = Flask(__name__)

# 글로벌 변수로 프레임을 저장
frame = None
frame_lock = threading.Lock()

def generate_frames():
    global frame
    cap = cv2.VideoCapture(0)

    while True:
        success, current_frame = cap.read()
        if not success:
            break  # 비디오가 끝나면 종료

        # 영상 크기 축소 (예시: 1/4 크기로 줄이기)
        current_frame = cv2.resize(current_frame, (current_frame.shape[1] // 4, current_frame.shape[0] // 4))

        # 새로운 프레임을 글로벌 변수에 저장
        with frame_lock:
            frame = current_frame.copy()

        # JPEG 형식으로 변환
        ret, buffer = cv2.imencode('.jpg', current_frame)
        current_frame = buffer.tobytes()

        # MJPEG 스트리밍 응답 반환
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n')

    cap.release()

def display_video():
    global frame
    while True:
        if frame is not None:
            # 현재 프레임을 OpenCV 윈도우로 표시
            cv2.imshow("Stream", frame)
            
            # 'q' 키를 누르면 스트리밍을 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

# 비디오 디스플레이를 위한 별도의 스레드 시작
threading.Thread(target=display_video, daemon=True).start()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
