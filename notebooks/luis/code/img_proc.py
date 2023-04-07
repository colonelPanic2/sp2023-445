import threading,time,signal,cv2,imutils,traceback,argparse,queue
from collections import deque
import numpy as np
import torch # NOTE: torch is not particularly useful at the moment
from helpers import writefile
TL = 0 # Top-left region of camera view
TM = 1 # Top-middle region of camera view
TR = 2 # Top-right region of camera view
BL = 3 # Bottom-left region of camera view
BM = 4 # Bottom-middle region of camera view
BR = 5 # Bottom-right region of camera view

def map_to_block_index(col_row,dims=(720,1278)):
    col_blocks = dims[1]//3
    row_blocks = dims[0]//2
    region_index = (col_row[0]//col_blocks) + 3*(col_row[1]>=row_blocks)
    return region_index
class images:
    def __init__(self,cam,demo=True):
        global sigint
        sigint = False
        self.camera_ = cam
        # This array will keep track of where the ball is located in the 6 regions
        # Of the camera view. The ball can be in multiple regions at once.
        self.regions= { TL:0, TM:0, TR:0, BL:0, BM:0, BR:0 }
        self.last_regions = list(self.regions.values())
        self.goal_timelimits = {'ball':5,'user':2,'waitpoint':2}
        self.timers = {TL:0, TM:0, TR:0, BL:0, BM:0, BR:0}
        self.demo=demo
        self.camera_.start_read()
    # def demo_(self,demo):
    #     self.demo = demo
    #     self.cam.demo = demo
    def update_goal_position(self,goal,t0=None):
        global sigint
        # NOTE: at the moment, the position only accounts for the center of the ball.
        position_xy,image = self.camera_.getimage() #torch.randint(0,255,(1280,720)) # Get image from camera
        if position_xy is not None:
            # image = torch.from_numpy(image) # Might be of some use later
            # Find the region(s) in which the ball was located, if it was
            # in the frame NOTE: need to update this to include all regions
            # that the ball is in, not just the center of the ball
            region_index = map_to_block_index(position_xy,image.shape)
            goal_positions = [region_index]
        else:
            goal_positions = [6] # The goal is not in the image
        if self.demo:
            self.camera_.show_tracking(image,position_xy)
        # # NOTE: Saving this part for non-hardware simulation/testing
        # # ball_position>5 is the case in which the ball isn't on the screen   
        # goal_positions = random.choices(list(range(7)),k=2) 
        
        # Only change the last location of the goal if the goal 
        # is currently in the camera view
        if not (all(pos==6 for pos in goal_positions)):# or all(pos>5 for pos in goal_positions)):
            self.last_regions = list(self.regions.values())
        # Change the current goal position
        if t0 is None:
            # If we only want the position of the goal without timing data,
            # then update the positions
            for i in range(6):
                if i in goal_positions:
                    self.regions[i]+= 1
                else:
                    self.regions[i]=0
            return None
        else:
            for i in range(6):
                if self.timers[i]==0:
                    self.timers[i]=t0
                if i in goal_positions:# and t0-self.timers[i]<self.goal_timelimits[goal]:
                    self.regions[i]+= 1
                    # COMMENT OUT OR REMOVE THIS FOR FINAL DEMO
                    print('\033[F\033[K' * 1, end = "")
                    print(f"{i}: {t0-self.timers[i]:.2f}")
                else:
                    self.regions[i]=0
                    self.timers[i] = t0
            return [t0-self.timers[i] for i in range(6)]
    # This function shouldn't need to be changed for image processing
    def get_goal_regions(self):
        # If the goal is in the camera view, then find the region(s) where it is present
        if not all(self.regions[i]==0 for i in range(6)):
            return [i for i in range(6) if self.regions[i]>0]
        # Otherwise, get the last known region(s) in which the goal was in the camera view
        return [j for j in range(6) if self.last_regions[j]>0]
        
class camera(images):
    def __init__(self,demo=True,init_time=None,logfile=None):
        global sigint
        sigint = False
        self.init_time = init_time
        self.logfile = logfile
        writefile(self.logfile,"Initializing camera...  ")
        self.cam = cv2.VideoCapture(0,cv2.CAP_V4L2)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
        # self.ap = argparse.ArgumentParser()
        # self.ap.add_argument("-v", "--video",
        #     help="path to the (optional) video file")
        #     #was 64
        # self.ap.add_argument("-b", "--buffer", type=int, default=32,
        #     help="max buffer size")
        # self.args = vars(self.ap.parse_args())
        self.greenLower = (30, 86, 46)
        self.greenUpper = (100, 255, 255)
        # self.pts = deque(maxlen=self.args["buffer"])
        self.q = queue.Queue()
        super().__init__(self,demo)
        writefile(self.logfile,"Done.\n")
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
    def start_read(self):
        self.capture_t = threading.Thread(target=self.camera_read)
        self.capture_t.start()
    # NOTE: May need to be more complex later
    def destroy(self):
        global sigint
        writefile(self.logfile,"\nHalting program...  ")
        sigint = True
        self.cam.release()
        if self.demo:
            cv2.destroyAllWindows()
        raise KeyboardInterrupt
        # Extra teardown work?
    def camera_read(self):
        global sigint
        while sigint==False:
            ret,frame = self.cam.read()
            if self.q.empty() and ret:
                self.q.put(frame)
        return
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
        global sigint
        center = None
        image=None
        while sigint==False:
            if not self.q.empty():
                image = self.q.get()
                center = self.old_balltrack(image) # NOTE: switch between 'old_balltrack' and 'new_balltrack' to see differences in results
                # update the points queue
                # self.pts.appendleft(center)
                # if self.demo:
                #     # NOTE: comment this out when not doing a demo
                #     self.show_tracking(image)
                break
        return center,image
    def show_tracking(self,image,position_xy):
        #delete this for final project
        # loop over the set of tracked points
        # for i in range(1, len(self.pts)):
        #     # if either of the tracked points are None, ignore
        #     # them
        #     if self.pts[i - 1] is None or self.pts[i] is None:
        #         continue
            # otherwise, compute the thickness of the line and
            # draw the connecting lines
            # thickness = int(np.sqrt(self.args["buffer"] / float(i + 1)) * 2.5)
            # cv2.line(image, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
        # Draw lines to show the regions of the screen
        cv2.namedWindow("Camera",cv2.WINDOW_FREERATIO)
        height, width = image.shape[:2]
        cv2.line(image, (width//3, 0), (width//3, height), (0, 0, 255), 2)
        cv2.line(image, (2*width//3, 0), (2*width//3, height), (0, 0, 255), 2)
        cv2.line(image, (0, height//2), (width, height//2), (0, 0, 255), 2)
        if position_xy is not None:
            region_map = [(0,0), (width//3,0),(2*width//3,0),(0,height//2),(width//3,height//2),(2*width//3,height//2)]
            block_index = map_to_block_index(position_xy)
            top_right = region_map[block_index]
            bottom_left = (top_right[0]+width//3,top_right[1]+height//2)
            cv2.rectangle(image,top_right,bottom_left,(0,255,0),2)
        # show the frame to our screen
        cv2.imshow("Camera", image)
        key = cv2.waitKey(1) & 0xFF
        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            self.destroy()
        return
# Special function for testing the image processing code directly
def iproc_main():
    global sigint
    sigint=False
    import time
    from helpers import logdata
    init_time,logfile,errfile = logdata()
    iproc = camera(demo=True,init_time=init_time,logfile=logfile)
    try:
        while sigint==False:
            t0 = time.perf_counter()
            iproc.update_goal_position('ball',time.time())
            iproc.get_goal_regions()
            # if sigint==False:
            #     print('\033[F\033[K' * 1, end = "")
            #     print(f"FPS: {1/(time.perf_counter()-t0):.2f}")
    except KeyboardInterrupt:
        writefile(logfile,'Done.')
        print("\nTerminated by user input.")
    except Exception as e:
        iproc.destroy() # Free the threads
        writefile(errfile,f"ERROR: {e}\n\n")
        backtrace = traceback.format_exc()
        writefile(errfile,backtrace + '\n')
        return 0


if __name__=='__main__':
    iproc_main()
