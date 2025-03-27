import cv2
import requests
import numpy as np

url = "http://127.0.0.1:5000/video_feed"

stream = requests.get(url, stream=True)
bytes_buffer = b""

for chunk in stream.iter_content(chunk_size=1024):
    bytes_buffer += chunk
    a = bytes_buffer.find(b'\xff\xd8')  # JPEG 시작 마커
    b = bytes_buffer.find(b'\xff\xd9')  # JPEG 끝 마커
    
    if a != -1 and b != -1:
        jpg = bytes_buffer[a:b+2]
        bytes_buffer = bytes_buffer[b+2:]

        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            # 클라이언트에서도 절반 크기로 조정 가능
            img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
            cv2.imshow("MJPEG Stream", img)
            if cv2.waitKey(1) == 27:  # ESC 키를 누르면 종료
                break

cv2.destroyAllWindows()
