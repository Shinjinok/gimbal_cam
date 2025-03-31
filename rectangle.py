from flask import Flask, Response
import cv2

app = Flask(__name__)

# MJPEG 스트리밍을 위한 비디오 캡처 객체 (웹캠 사용)
cap = cv2.VideoCapture(0)  # '0'은 기본 웹캠

# 스트리밍할 프레임을 생성하는 함수
def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # MJPEG 형식으로 프레임을 인코딩
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # MJPEG 스트리밍 포맷으로 반환
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# 메인 페이지 라우트 - 스트리밍을 위한 HTML 렌더링
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MJPEG 스트리밍</title>
    </head>
    <body>
        <h1>MJPEG 스트리밍</h1>
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
    </body>
    </html>
    '''

# MJPEG 스트림을 처리하는 라우트
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
