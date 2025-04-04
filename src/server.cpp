#include <opencv2/opencv.hpp>
#include <opencv2/tracking.hpp>
#include <opencv2/tracking/tracking_legacy.hpp>
#include "civetweb.h"
#include <iostream>
#include <sstream>
#include <atomic>
#include <thread>

using namespace cv;
using namespace std;
using namespace std::this_thread;
atomic<int> gx(0), gy(0); // 마우스 클릭 좌표
atomic<bool> tracking_initialized(false);
Rect2d roi;
Ptr<legacy::tracking::TrackerMOSSE> tracker = legacy::tracking::TrackerMOSSE::create();
VideoCapture cap(0);

// MJPEG 스트리밍 처리
static int video_stream(struct mg_connection *conn, void *) {
    mg_printf(conn, "HTTP/1.1 200 OK\r\n"
                    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
                    "Cache-Control: no-cache\r\n"
                    "Pragma: no-cache\r\n\r\n");

    Mat frame;
    vector<uchar> buffer;

    while (cap.isOpened()) { 
        cap >> frame;
        if (frame.empty()) break;

        // 트래킹 수행
        if (tracking_initialized) {
            bool success = tracker->update(frame, roi);
            if (success) rectangle(frame, roi, Scalar(0, 255, 0), 2);
        }

        // 화면에 출력 (imshow)
        imshow("Video Feed", frame); // "Video Feed"라는 이름의 창에 영상 표시

        imencode(".jpg", frame, buffer);
        mg_printf(conn, "--frame\r\n"
                        "Content-Type: image/jpeg\r\n"
                        "Content-Length: %zu\r\n\r\n", buffer.size());
        mg_write(conn, buffer.data(), buffer.size());
        mg_printf(conn, "\r\n");

        // 사용자가 'q' 키를 누르면 비디오 스트리밍을 종료
        if (waitKey(1) == 'q') {
            break;
        }

        this_thread::sleep_for(chrono::milliseconds(30));
    }
    return 1;
}

// 클릭 이벤트 처리
static int click_event(struct mg_connection *conn, void *ignored) {
    char post_data[1024];
    mg_read(conn, post_data, sizeof(post_data));

    int x, y;
    sscanf(post_data, "{\"click_x\":%d,\"click_y\":%d}", &x, &y);
    gx = x;
    gy = y;

    Mat frame;
    cap >> frame;
    if (!frame.empty()) {
        roi = Rect2d(gx - 50, gy - 50, 100, 100);
        tracker = legacy::tracking::TrackerMOSSE::create();
        tracker->init(frame, roi);
        tracking_initialized = true;
    }

    mg_printf(conn, "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n\r\n"
                    "{\"status\":\"success\"}");
    return 200;
}

int main() {
    if (!cap.isOpened()) {
        cerr << "카메라를 열 수 없습니다!" << endl;
        return -1;
    }
    else cout << "카메라를 열었습니다." << endl;

    struct mg_callbacks callbacks = {0};
    struct mg_context *ctx;
    struct mg_option options[] = {
        {"document_root", MG_CONFIG_TYPE_STRING, "."},     // 기본 경로 설정
        {"listening_ports", MG_CONFIG_TYPE_STRING, "8080"}, // 기본 포트 설정
        {nullptr, 0, nullptr}                               // 배열의 끝을 나타냄
    };
    // `const char*` 배열로 변환
    std::vector<const char*> option_strings;
    for (int i = 0; options[i].name != nullptr; ++i) {
        // 각 설정을 "name=value" 형식으로 변환하여 추가
        std::string option = std::string(options[i].name) + "=" + options[i].default_value;
        option_strings.push_back(option.c_str());
    }

    // `nullptr`을 마지막에 추가
    option_strings.push_back(nullptr);
    ctx = mg_start(&callbacks, nullptr, option_strings.data());
    mg_set_request_handler(ctx, "/video_feed", video_stream, nullptr);
    mg_set_request_handler(ctx, "/click", click_event, nullptr);

    cout << "서버 실행 중: http://localhost:8080" << endl;
    while (true) {
        this_thread::sleep_for(chrono::seconds(1));
    }
    cout << "서버 중지" << endl;
    mg_stop(ctx);
    cap.release();
    destroyAllWindows(); // 모든 OpenCV 창 닫기
    return 0;
}
