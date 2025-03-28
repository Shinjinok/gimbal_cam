ffmpeg -i chase.mp4 \
  -filter_complex "[0:v]split=2[stream1][stream2]; \
  [stream1]scale=1920x1080[stream1out]; \
  [stream2]scale=640x360[stream2out]" \
  -map "[stream1out]" -c:v libx264 -f rtsp rtsp://localhost:8554/stream1 \
  -map "[stream2out]" -c:v libx264 -f rtsp rtsp://localhost:8554/stream2
