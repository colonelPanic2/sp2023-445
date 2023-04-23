import threading,cv2,imutils,traceback,queue
from sys import platform
import signal,time

from helpers.helpers import writefile,map_to_block_index,teardown_timeout_handler,time_data
TLL,TLM,TLR = 0,  1, 2 # Top-left region of camera view
TML,TMM,TMR = 3,  4, 5 # Top-middle region of camera view
TRL,TRM,TRR = 6,  7, 8 # Top-right region of camera view
BLL,BLM,BLR = 9, 10,11 # Bottom-left region of camera view
BML,BMM,BMR = 12,13,14 # Bottom-middle region of camera view
BRL,BRM,BRR = 15,16,17 # Bottome-right region of camera view
class images:
    def __init__(self,cam):
        global sigint
        sigint = False
        self.camera_ = cam
        # This array will keep track of where the ball is located in the 6 regions
        # Of the camera view. The ball can be in multiple regions at once.
        self.regions,self.timers = {},{}
        for r in range(18):
            self.regions[r]=0
            self.timers [r]=0
        self.last_regions = list(self.regions.values())
        self.goal_timelimits = {'ball_W':2,'ball_C':0,'ball_A':2,'user':1,'waitpoint':1} # I don't expect that we'll need time limits for the user or the waitpoint
        self.camera_.start_read()
        return
    def update_goal_position(self,goal,t0=None):
        global sigint
        position_xy,image = self.camera_.getimage(goal)
        if position_xy is not None:
            region_index = map_to_block_index(position_xy,image.shape)
            goal_positions = [region_index]
        else:
            goal_positions = [18] # The goal is not in the image
        if self.camera_.demo:
            self.camera_.show_tracking(image,position_xy)
        # Only update the last location of the goal if the goal 
        # is currently in the camera view
        if not (all(pos==18 for pos in goal_positions)):
            self.last_regions = list(self.regions.values())
        for i in range(18):
            if self.timers[i]==0:
                self.timers[i]=t0
            if i in goal_positions:
                self.regions[i]+= 1
                # if not self.camera_.noprint:
                #     print('\033[F\033[K' * 1, end = "")
                #     print(f"{i}: {t0-self.timers[i]:.2f}")
            else:
                self.regions[i]=0
                self.timers[i] = t0
        return [t0-self.timers[i] for i in range(18)]
    # Get the relevant positional data for the goal.
    def get_goal_regions(self):
        # If the goal is in the camera view, then find the region(s) where it is present
        # if not all(self.regions[i]==0 for i in range(18)):
        return [i for i in range(18) if self.regions[i]>0]
        # Otherwise, get the last known region(s) in which the goal was in the camera view
        # return [j for j in range(18) if self.last_regions[j]>0]
        
class camera(images):
    def __init__(self,noprint,demo,manual,init_time,logfile):
        writefile(logfile,"Initializing camera...  ")
        global sigint
        self.capture_t = None
        sigint = False
        self.noprint=noprint
        self.demo=demo
        self.manual=manual
        self.init_time = init_time
        self.logfile = logfile
        self.index = 0 # NOTE: Keep track of the camera being used (front=0, back=1)
        self.index_factor = [1,2][int(platform=='linux')]
        cam_backends=[cv2.CAP_DSHOW,cv2.CAP_V4L2] #Linux and Windows camera backends
        self.cam = cv2.VideoCapture(self.index*self.index_factor,cam_backends[int(platform=='linux')]) 
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1917)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
        self.redLower = (140, 70, 70)
        self.redUpper = (179, 255, 255)
        self.greenLower = (30, 86, 46)
        self.greenUpper = (100, 255, 255)
        self.blueLower = (40, 50, 80)
        self.blueUpper = (130, 255, 255)
        self.q = queue.Queue()
        super().__init__(self)
        writefile(self.logfile,"Done.\n")
    def camswitch(self):
        global sigint
        # if self.capture_t!=None:
        #     sigint=True
        #     self.capture_t.join()
        #     sigint=False
        #     self.cam.release()
        #     while not self.q.empty():
        #         _ = self.q.get()
        self.index = int(not self.index)
        cam_backends=[cv2.CAP_DSHOW,cv2.CAP_V4L2] #Linux and Windows camera backends
        # NOTE: multiply the self.index by 2 when on the Pi
        self.cam = cv2.VideoCapture(self.index*self.index_factor,cam_backends[int(platform=='linux')])            
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1917) # Divides evenly by 9
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
        self.start_read()
    # NOTE: This function is still unused because I don't quite know how to use
    # it. I'll have to ask yinhuo for help with integrating this into the design.
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
    # Spawn a camera thread to constantly read the camera's input.
    def start_read(self):
        # self.capture_t = threading.Thread(target=self.camera_read)
        # self.capture_t.start()
        pass
    # Tell the camera thread to end smoothly, and raise a KeyboardInterupt
    # that will be caught in the 'main_fetching' function in main.py
    def destroy(self):
        global sigint
        print("\nHalting program...")
        writefile(self.logfile,"\nHalting program...  ")
        sigint = True
        if platform=='linux':
            signal.signal(signal.SIGALRM, teardown_timeout_handler)
            signal.alarm(2)
        if self.demo:
            cv2.destroyAllWindows()
        # NOTE: This doesn't seem to be causing any problems, but it doesn't seem to 
        # help much, either. There is an occasional error added as a manual entry near 
        # the end of the err.txt log for 04-08.
        # print("Joining camera thread and main thread...",end='  ')
        # with threading.Lock():
        #     if self.capture_t is not None and self.capture_t.is_alive():
        #         self.capture_t.join()
        if platform=='linux':
            signal.alarm(0)
        self.cam.release()
        # print('thread join successful')
        writefile(self.logfile,'\nDone.\nRaising KeyboardInterrupt to end the process...\n')
        raise KeyboardInterrupt
    # (camera thread) Read an image from the camera and store it in 
    # a queue to be accessed by the main thread in the 'getimage' function.
    def camera_read(self):
        global sigint
        while sigint==False:
            ret,frame = self.cam.read()
            if self.q.empty() and ret:
                self.q.put(frame)
        return
    # NOTE: Old ball tracking (consistent, but OVERLY sensitive to non-ball objects with a similar color)
    def track(self,frame,goal):   
        center = None
        blurred = cv2.GaussianBlur(frame, (11,11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        if goal[:4]=='ball':
            mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
        elif goal=='user':
            mask = cv2.inRange(hsv, self.redLower, self.redUpper)
        elif goal=='waitpoint':
            mask = cv2.inRange(hsv, self.blueLower, self.blueUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,\
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
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
    def new_track(self,frame,goal):
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        if goal[:4]=='ball':
            mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
        elif goal=='user':
            mask = cv2.inRange(hsv, self.redLower, self.redUpper)
        elif goal=='waitpoint':
            mask = cv2.inRange(hsv, self.blueLower, self.blueUpper)
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
    # (main thread) Get an image from the camera thread by accessing a shared queue, and
    # use it to determine the (x,y) coordinates of the center of the goal. If the goal
    # isn't detected in the image, then center = None.
    def getimage(self,goal):
        global sigint
        center = None
        image=None
        while sigint==False:
            ret,image=self.cam.read()
            if ret:
            # if not self.q.empty():
                # image = self.q.get()
                center = self.track(image,goal) # NOTE: switch between 'track' and 'new_track' to see differences in results
                break
        return center,image
    # Draw the lines showing the 18 regions of the image. If the goal is in a region,
    # then outline the region in green. Otherwise, outline it in red.
    def show_tracking(self,image,position_xy):
        if image is not None:
            # Draw lines to show the regions of the screen
            cv2.namedWindow("Camera",cv2.WINDOW_FREERATIO)
            height, width = image.shape[:2]

            # Calculate the scale factor to fit the image inside the window
            scale_factor = min(1, 800 / width, 600 / height)  # 800x600 is the size of the window

            # Resize the image with the calculated scale factor
            resized_img = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)
            height,width = resized_img.shape[:2]
            for i in range(1,9):
                cv2.line(resized_img, (i*(width//9), 0), (i*(width//9), height), (0, 0, 255), 2)
            cv2.line(resized_img, (0, height//2), (width, height//2), (0, 0, 255), 2)
            if position_xy is not None:
                block_index = map_to_block_index(position_xy,resized_img.shape)
                if block_index<18:
                    # for y in range(2):
                    region_map = {}
                    for r in range(9):
                        region_map[r]  = (r*(width//9),0)
                        region_map[r+9]= (r*(width//9),height//2)
                    top_left = region_map[block_index]
                    bottom_right = (top_left[0]+width//9,top_left[1]+height//2)
                    cv2.rectangle(resized_img,top_left,bottom_right,(0,255,0),2)
                else:
                    print(f"\nUnexpected position value: map_to_block_index({position_xy}) -> {block_index}\n")
            # show the frame to our screen
            cv2.imshow("Camera", resized_img)
            key = cv2.waitKey(1) & 0xFF
            # if the 'q' key is pressed, stop the loop
            if self.manual==0:
                if key == ord("q"):
                    self.destroy()
                elif self.demo==1:
                    if key == ord('c') :
                        self.camswitch()
                    elif key == ord('2') and platform=='linux':
                        signal.raise_signal(signal.SIGUSR2)
        return
    



try:
    def microcontroller_CTRL_ACK_handler(signum,frame): # SIGUSR1
        signal.signal(signal.SIGUSR1,signal.SIG_IGN)
        global ctrl 
        if ctrl.gettimes is not None:
            t1 = time.time()
            # print(f"{t1} - {ctrl.INT_start_time} = {t1 - ctrl.INT_start_time}")
            time_data([ctrl.gettimes,ctrl.INT_start_time,t1],'fsm.get_state()',4)
            ctrl.INT_start_time=0
        ctrl.DONE = True
        # print(ctrl.DONE,'\n')
        signal.signal(signal.SIGUSR1,microcontroller_CTRL_ACK_handler)
    def microcontroller_PROX_handler(signum,frame): # SIGUSR2
        signal.signal(signal.SIGUSR2,signal.SIG_IGN)
        global ctrl
        ctrl.proximity = int(not ctrl.proximity)
        print(ctrl.proximity,'\n')
        signal.signal(signal.SIGUSR2,microcontroller_PROX_handler)
except:
    pass

# Special function for testing the image processing code directly
def iproc_main():
    global sigint
    global ctrl
    sigint=False
    import time
    try:
        from gpio import control
    except:
        pass
    from sys import argv
    if len(argv[1:]) == 0:
        args='ball'
    else:
        args=argv[1]
    try:
        cam = camera(                        noprint=0,demo=1,manual=1,init_time=0,logfile='cam-dot-py-logfile')
        try:
            ctrl = control(    gettimes=None,noprint=0,demo=1,manual=1,init_time=0,logfile='cam-dot-py-logfile') 
            signal.signal(signal.SIGUSR1, microcontroller_CTRL_ACK_handler)
            signal.signal(signal.SIGUSR2, microcontroller_PROX_handler)
            ctrl.init_manual_control(cam)
            # 'ctrl' will be in the main loop of the manual control mode until it is escaped with CTRL+C,
            # after which we will no longer be in manual control mode
            ctrl.manual=0
        except:
            print("You're not on Linux, or an unexpected exception occurred in iproc_main() while initializing 'control'")
        cam.manual=0
        while sigint==False:
            t0 = time.perf_counter()
            cam.update_goal_position(args,time.time())
            cam.get_goal_regions()
            if sigint==False and platform=='linux':
                print('\033[F\033[K' * 1, end = "")
                print(f"FPS: {1/(time.perf_counter()-t0):.2f}")
    except KeyboardInterrupt:
        writefile('cam-dot-py-logfile','Done.')
        print("\nDone.\nTerminated by user input.")
    except Exception as e:
        cam.destroy() # Free the threads
        try:
            ctrl.stop_all()
        except Exception as e2:
            print("COULDN'T DESTROY CONTROL INTERFACE")
            print(e2,'\n')
        writefile('errfile',f"ERROR: {e}\n\n")
        backtrace = traceback.format_exc()
        writefile('errfile',backtrace + '\n')
        return 0


if __name__=='__main__':
    iproc_main()
