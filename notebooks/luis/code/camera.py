import threading,time,signal,cv2,imutils,traceback,argparse,streamlink
from collections import deque
import numpy as np

class camera():
    def __init__(self):
        print("Initializing camera...")
        # self.cam = cv2.VideoCapture("rtmp://live.twitch.tv/app/live_733973012_UxcTGuiGVDvcs9ZqDxUVCHT57ZYkcX") # NOTE: Modified for faster connection on windows
        url = "twitch.tv/llllllllllldavila0"
        quality = '720p'
        # Open the stream
        stream_url = streamlink.streams(url)[quality].url
        self.cam = cv2.VideoCapture(stream_url)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)   
        self.lock = threading.Lock() 
        self.ap = argparse.ArgumentParser()
        self.ap.add_argument("-v", "--video",
            help="path to the (optional) video file")
            #was 64
        self.ap.add_argument("-b", "--buffer", type=int, default=32,
            help="max buffer size")
        self.args = vars(self.ap.parse_args())
        #original: (29, 86, 6) and (64, 255, 255)
        self.greenLower = (30, 86, 46)
        self.greenUpper = (100, 255, 255)
        #red and blue colorspace as well
        self.pts = deque(maxlen=self.args["buffer"])
        print("Done.")
    def release(self):
        self.cam.release()
    def start_read(self):
        self.capture_t = threading.Thread(target=self.camera_read)
        self.capture_t.start()
    # NOTE: May need to be more complex later
    def destroy(self):
        global sigint
        sigint = True
        print("\nHalting program...")
        # Extra teardown work?
        print("Done.")
    def camera_read(self):
        global image
        global sigint
        while sigint==False:
            ret,frame = self.cam.read()
            t0 = time.perf_counter()
            if ret:
                image = frame
            # print('\033[F\033[K' * 1, end='')
            # print(f"Child: {time.perf_counter()-t0:.4f}, {threading.current_thread().ident}")
        return
    def getimage(self):
        global image
        global sigint
        position = None
        while image is None and sigint==False:
            if image is not None:
                blurred = cv2.GaussianBlur(image, (11, 11), 0)
                hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
                # construct a mask for the color "green", then perform
                # a series of dilations and erosions to remove any small
                # blobs left in the mask
                mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)
                
                # find contours in the mask and initialize the current
                # (x, y) center of the ball
                cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                center = None
                # only proceed if at least one contour was found
                if len(cnts) > 0:
                    # find the largest contour in the mask, then use
                    # it to compute the minimum enclosing circle and
                    # centroid
                    c = max(cnts, key=cv2.contourArea)
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    position = center # NOTE: if the goal is detected, then return its position instead of 'None'
                    # only proceed if the radius meets a minimum size
                    #original size as 10
                    if radius > 3:
                        # draw the circle and centroid on the frame,
                        # then update the list of tracked points
                        cv2.circle(image, (int(x), int(y)), int(radius),
                            (0, 255, 255), 2)
                        cv2.circle(image, center, 5, (0, 0, 255), -1)
                # update the points queue
                self.pts.appendleft(center)
                # NOTE: comment this out when not doing a demo
                self.show_tracking(image)
        out_img = image
        image=None
        return position,out_img
    def show_tracking(self,image):
        #delete this for final project
        # loop over the set of tracked points
        for i in range(1, len(self.pts)):
            # if either of the tracked points are None, ignore
            # them
            if self.pts[i - 1] is None or self.pts[i] is None:
                continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            thickness = int(np.sqrt(self.args["buffer"] / float(i + 1)) * 2.5)
            cv2.line(image, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
        # show the frame to our screen
        cv2.imshow("Camera", image)
        key = cv2.waitKey(1) & 0xFF
        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            self.destroy()
        return
def signal_handler(signum,frame):
    global sigint
    sigint = True
    global cam
    print("Process terminated.")
    exit(0)

def main():
    global sigint
    sigint = False
    global image
    image = None
    global cam
    signal.signal(signal.SIGINT, signal_handler)
    cam = camera()
    try:
        cam.start_read()
        # In the final version, we would call some main program that would
        # eventually call cam.getimage(), instead of the following while loop
        while sigint==False:
            t0 = time.perf_counter()
            # TODO: We need to be able to keep track of when to switch between basic
            # color detection and ball tracking (or between the previous version of 
            # ball tracking and yinshuo's updated version)
            cam.getimage()
            print('\033[F\033[K' * 1, end = "")
            print(f"FPS: {1/(time.perf_counter()-t0):.2f}")
    except Exception as e:
        cam.destroy() # Free the threads
        print("ERROR:",e,end='\n\n')
        traceback.print_exc()
main()
