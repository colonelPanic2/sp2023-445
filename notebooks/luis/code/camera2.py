import time,signal,cv2,imutils,traceback,argparse,multiprocessing,os
from collections import deque
import numpy as np

class camera():
    def __init__(self):
        print("Initializing camera...")
        self.stop_loop = False
        self.cam = cv2.VideoCapture(0,cv2.CAP_V4L2)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)   
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
        self.q = multiprocessing.Queue()
        self.stop_q = multiprocessing.Queue()
        self.camera_process = multiprocessing.Process(target=self.camera_read,args=(self.q,self.stop_q,))
        self.camera_process.start()
        print("Done.")
    # NOTE: This isn't working quite as well as I had hoped. Calling this
    # function on its own doesn't seem to free the process.
    def destroy(self):
        self.stop_loop=True
        print("\nCamera: Halting subprocess...")
        self.stop_q.put(None)
        self.q.close()
        self.stop_q.close()
        print("Done.")
    def camera_read(self,q,stop_q):
        while stop_q.empty():
            if q.empty() and stop_q.empty():
                ret,frame = self.cam.read()
                if ret:
                    q.put(frame)
        return
    def detect_shape(self,c):
        shape = "empty"
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        # Triangle
        if len(approx) == 3:
            shape = "triangle"
        # Square or rectangle
        elif len(approx) == 4:
            (x, y, w, h) = cv2.boundingRect(approx)
            ar = w / float(h)
        # A square will have an aspect ratio that is approximately
        # equal to one, otherwise, the shape is a rectangle
            shape = "rectangle"
        # Pentagon
        elif len(approx) == 5:
            shape = "pentagon"
        # Otherwise assume as circle or oval
        else:
            (x, y, w, h) = cv2.boundingRect(approx)
            shape = "circle"
        return shape

    # NOTE: Old ball tracking (consistent, but OVERLY sensitive to non-ball objects with a similar color)
    def old_balltrack(self,frame):        
        blurred = cv2.GaussianBlur(frame, (11,11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,\
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        center = None
        if len(cnts) > 0:
            position = None
            c = max(cnts, key=cv2.contourArea)
            ((x,y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            if radius > 3:
                cv2.circle(frame, (int(x), int(y)), int(radius),\
                           (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0,0,255), -1)
        return center
    # NOTE: New ball tracking (inconsistent, but LESS sensitive to non-ball objects with similar color)
    def new_balltrack(self,frame):
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
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
            for c in cnts:
                shape = self.detect_shape(c)
                if shape == "circle" :
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    # only proceed if the radius meets a minimum size
                    #original size as 10
                    if radius > 3:
                        # draw the circle and centroid on the frame,
                        # then update the list of tracked points
                        cv2.circle(frame, (int(x), int(y)), int(radius),
                            (0, 255, 255), 2)
                        cv2.circle(frame, center, 5, (0, 0, 255), -1)
        return center
    def getimage(self):
        center,image = None, None
        while self.stop_q.empty():
            if not self.q.empty():
                image = self.q.get()
                center = self.new_balltrack(image) # NOTE: switch between 'old_balltrack' and 'new_balltrack' to see differences in results
                # update the points queue
                self.pts.appendleft(center)
                # NOTE: comment this out when not doing a demo
                self.show_tracking(image)
                break
        return center,image
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
            raise KeyboardInterrupt
        return

def signal_handler(signum,frame):
    global cam
    cam.destroy()
    exit(0)



def main():
    global cam
    cam = camera()
    global sigint
    sigint = False
    signal.signal(signal.SIGINT, signal_handler)
    try:
        try:
            # In the final version, we would call some main program that would
            # eventually call cam.getimage(), instead of the following while loop
            while cam.stop_loop==False:
                t0 = time.perf_counter()
                # TODO: We need to be able to keep track of when to switch between basic
                # color detection and ball tracking (or between the previous version of 
                # ball tracking and yinshuo's updated version)
                position,_ = cam.getimage()
                print('\033[F\033[K' * 1, end = "")
                print(f"FPS: {1/(time.perf_counter()-t0):.2f}")
        except KeyboardInterrupt as e:
            # import warnings
            # with warnings.catch_warnings():
            #     warnings.simplefilter("ignore",category=Warning)
            # NOTE: As of right now, this is the only way to stop the processes,
            # but it generates a warning that can't be ignored even though this
            # call doesn't seem to have any consequences.
            os.kill(0,signal.SIGINT)
    except Exception as e:
        cam.destroy() # Free the threads
        print("ERROR:",e,end='\n\n')
        traceback.print_exc()
main()

