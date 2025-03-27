from flask import Flask, Response
import cv2

app = Flask(__name__)

def generate_frames():
    cap = cv2.VideoCapture(1)  # 웹캠 사용 (0번 카메라)
    while True:
        success, frame = cap.read()
        if not success:
            break
        # 영상 크기를 절반으로 축소
        frame = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2))
        # JPEG 형식으로 변환
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # MJPEG 스트리밍 응답
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
