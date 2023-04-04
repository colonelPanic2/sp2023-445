import cv2,streamlink
# cap = cv2.VideoCapture("live_733973012_HUd6dB0TlMVDzFzfvS94lHKrVdw63H")
import subprocess

# Start FFmpeg and pipe the output to stdout
# cmd = "ffmpeg -i rtmp://live.twitch.tv/app/live_733973012_HUd6dB0TlMVDzFzfvS94lHKrVdw63H -c copy -f h264 -"
# p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
url = "twitch.tv/ironmouse"
quality = '720p'
# Open the stream
stream_url = streamlink.streams(url)[quality].url

cap = cv2.VideoCapture(stream_url)

# Extract frames from the stream
while True:
    ret, image = cap.read()
    if ret:
        cv2.imshow("Stream",image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Stop reading")
            break

