import threading,cv2,imutils,traceback,queue
from sys import platform
import signal,time
from os import kill,getpid
from helpers.helpers import writefile,map_to_block_index,teardown_timeout_handler,time_data
TLL,TLM,TLR = 0,  1, 2 # Top-left region of camera view
TML,TMM,TMR = 3,  4, 5 # Top-middle region of camera view
TRL,TRM,TRR = 6,  7, 8 # Top-right region of camera view
BLL,BLM,BLR = 9, 10,11 # Bottom-left region of camera view
BML,BMM,BMR = 12,13,14 # Bottom-middle region of camera view
BRL,BRM,BRR = 15,16,17 # Bottome-right region of camera view
class images:
    def __init__(self,cam):
        self.camera_ = cam
        self.regions,self.timers = {},{}
        for r in range(6):
            self.regions[r]=0
            self.timers [r]=0
        self.last_regions = list(self.regions.values())
        self.goal_timelimits = {'ball_W':2,'ball_C':0,'ball_A':0.5,'user':0,'waitpoint':0} 
        return
    def update_goal_position(self,goal,t0=None):
        position_xy,image = self.camera_.getimage(goal)
        if position_xy is not None:
            region_index = map_to_block_index(position_xy,image.shape)
            goal_positions = [region_index]
        else:
            goal_positions = [6] # The goal is not in the image
        if self.camera_.demo:
            self.camera_.show_tracking(image,position_xy)
        # Only update the last location of the goal if the goal 
        # is currently in the camera view
        if not (all(pos==6 for pos in goal_positions)):
            self.last_regions = list(self.regions.values())
        for i in range(6):
            if self.timers[i]==0:
                self.timers[i]=t0
            if i in goal_positions:
                self.regions[i]+= 1
                # if not self.camera_.noprint:
                #     print('\033[F\033[K' * 1, end = "")
                #     print(f"{i}: {t0-self.timers[i]:.2f}")
            else:
                self.timers[i] = t0
                self.regions[i]=0
        return [t0-self.timers[i] for i in range(6)]
    # Get the relevant positional data for the goal.
    def get_goal_regions(self):
        return [i for i in range(6) if self.regions[i]>0]
        
class camera(images):
    def __init__(self,noprint,demo,manual,init_time,logfile):
        writefile(logfile,"Initializing camera...  ")
        self.capture_t = None
        self.noprint=noprint
        self.demo=demo
        self.manual=manual
        self.init_time = init_time
        self.logfile = logfile
        self.index = 0 # NOTE: Keep track of the camera being used (front=0, back=1)
        self.index_factor = [1,2][int(platform=='linux')]
        cam_backends=[cv2.CAP_DSHOW,cv2.CAP_V4L2] #Linux and Windows camera backends
        self.cam = cv2.VideoCapture(self.index*self.index_factor,cam_backends[int(platform=='linux')]) 
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
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
        self.index = int(not self.index)
        cam_backends=[cv2.CAP_DSHOW,cv2.CAP_V4L2] #Linux and Windows camera backends
        # NOTE: multiply the self.index by 2 when on the Pi
        self.cam = cv2.VideoCapture(self.index*self.index_factor,cam_backends[int(platform=='linux')])            
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # Divides evenly by 3
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
    # Tell the camera thread to end smoothly, and raise a KeyboardInterupt
    # that will be caught in the 'main_fetching' function in main.py
    def destroy(self):
        print("\nHalting program...")
        writefile(self.logfile,"\nHalting program...  ")
        if platform=='linux':
            signal.signal(signal.SIGALRM, teardown_timeout_handler)
            signal.alarm(2)
        self.cam.release()
        if self.demo:
            cv2.destroyAllWindows()
        if platform=='linux':
            signal.alarm(0)
        writefile(self.logfile,'\nDone.\nRaising KeyboardInterrupt to end the process...\n')
        raise KeyboardInterrupt
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
    def getimage(self,goal):
        center = None
        image=None
        while True:
            ret,image=self.cam.read()
            if ret:
                center = self.track(image,goal)
                break
        return center,image
    # Draw the lines showing the 18 regions of the image. If the goal is in a region,
    # then outline the region in green. Otherwise, outline it in red.
    def show_tracking(self,image,position_xy):
        if image is not None:
            # Draw lines to show the regions of the screen
            cv2.namedWindow("Camera",cv2.WINDOW_FREERATIO)
            height, width = image.shape[:2]
            for i in range(1,3):
                cv2.line(image, (i*(width//3), 0), (i*(width//3), height), (0, 0, 255), 2)
            cv2.line(image, (0, height//2), (width, height//2), (0, 0, 255), 2)
            if position_xy is not None:
                block_index = map_to_block_index(position_xy,image.shape)
                if block_index<6:
                    region_map = {}
                    for r in range(3):
                        region_map[r]  = (r*(width//3),0)
                        region_map[r+3]= (r*(width//3),height//2)
                    top_left = region_map[block_index]
                    bottom_right = (top_left[0]+width//3,top_left[1]+height//2)
                    cv2.rectangle(image,top_left,bottom_right,(0,255,0),2)
                else:
                    print(f"\nUnexpected position value: map_to_block_index({position_xy}) -> {block_index}\n")
            # show the frame to our screen
            cv2.imshow("Camera", image)
            key = cv2.waitKey(1) & 0xFF
            # if the 'x' key is pressed, stop the loop
            if self.manual==0:
                if key == ord("x"):
                    self.destroy()
                elif self.demo==1:
                    if key == ord('m'):
                        kill(getpid(),signal.SIGQUIT)
                    elif key == ord('c') :
                        self.camswitch()
                    # elif key == ord('2') and platform=='linux':
                    #     signal.raise_signal(signal.SIGUSR2)
        return
    



try:
    def microcontroller_CTRL_ACK_handler(signum,frame): # SIGUSR1
        signal.signal(signal.SIGUSR1,signal.SIG_IGN)
        global ctrl 
        if ctrl.gettimes is not None:
            t1 = time.time()
            time_data([ctrl.gettimes,ctrl.INT_start_time,t1],'fsm.get_state()',4)
            ctrl.INT_start_time=0
        ctrl.DONE = True
        signal.signal(signal.SIGUSR1,microcontroller_CTRL_ACK_handler)
    def microcontroller_PROX_handler(signum,frame): # SIGUSR2
        signal.signal(signal.SIGUSR2,signal.SIG_IGN)
        global ctrl
        ctrl.proximity = int(not ctrl.proximity)
        print(ctrl.proximity,'\n')
        signal.signal(signal.SIGUSR2,microcontroller_PROX_handler)
except:
    pass
def control_switch_handler(signum,frame):
    signal.alarm(0)
    global ctrl
    ctrl.control_switch()
# Special function for testing the image processing code directly
def iproc_main():
    global ctrl
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
        while True:
            t0 = time.perf_counter()
            cam.update_goal_position(args,time.time())
            cam.get_goal_regions()
            if platform=='linux':
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


# import threading,cv2,imutils,traceback,queue
# from sys import platform
# import signal,time
# from os import kill,getpid
# from helpers.helpers import writefile,map_to_block_index,teardown_timeout_handler,time_data
# TLL,TLM,TLR = 0,  1, 2 # Top-left region of camera view
# TML,TMM,TMR = 3,  4, 5 # Top-middle region of camera view
# TRL,TRM,TRR = 6,  7, 8 # Top-right region of camera view
# BLL,BLM,BLR = 9, 10,11 # Bottom-left region of camera view
# BML,BMM,BMR = 12,13,14 # Bottom-middle region of camera view
# BRL,BRM,BRR = 15,16,17 # Bottome-right region of camera view
# class images:
#     def __init__(self,cam):
#         self.camera_ = cam
#         self.regions,self.timers = {},{}
#         for r in range(18):
#             self.regions[r]=0
#             self.timers [r]=0
#         self.last_regions = list(self.regions.values())
#         self.goal_timelimits = {'ball_W':2,'ball_C':0,'ball_A':0.5,'user':0,'waitpoint':0} 
#         return
#     def update_goal_position(self,goal,t0=None):
#         position_xy,image = self.camera_.getimage(goal)
#         if position_xy is not None:
#             region_index = map_to_block_index(position_xy,image.shape)
#             goal_positions = [region_index]
#         else:
#             goal_positions = [18] # The goal is not in the image
#         if self.camera_.demo:
#             self.camera_.show_tracking(image,position_xy)
#         # Only update the last location of the goal if the goal 
#         # is currently in the camera view
#         if not (all(pos==18 for pos in goal_positions)):
#             self.last_regions = list(self.regions.values())
#         for i in range(18):
#             if self.timers[i]==0:
#                 self.timers[i]=t0
#             if i in goal_positions:
#                 self.regions[i]+= 1
#                 # if not self.camera_.noprint:
#                 #     print('\033[F\033[K' * 1, end = "")
#                 #     print(f"{i}: {t0-self.timers[i]:.2f}")
#             else:
#                 if not ((13<=i+1<=14 and i+1 in goal_positions)\
#                     or  (12<=i-1<=13 and i-1 in goal_positions)):
#                     self.timers[i] = t0
#                     self.regions[i]=0
#         return [t0-self.timers[i] for i in range(18)]
#     # Get the relevant positional data for the goal.
#     def get_goal_regions(self):
#         return [i for i in range(18) if self.regions[i]>0]
        
# class camera(images):
#     def __init__(self,noprint,demo,manual,init_time,logfile):
#         writefile(logfile,"Initializing camera...  ")
#         self.capture_t = None
#         self.noprint=noprint
#         self.demo=demo
#         self.manual=manual
#         self.init_time = init_time
#         self.logfile = logfile
#         self.index = 0 # NOTE: Keep track of the camera being used (front=0, back=1)
#         self.index_factor = [1,2][int(platform=='linux')]
#         cam_backends=[cv2.CAP_DSHOW,cv2.CAP_V4L2] #Linux and Windows camera backends
#         self.cam = cv2.VideoCapture(self.index*self.index_factor,cam_backends[int(platform=='linux')]) 
#         self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1917)
#         self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
#         self.redLower = (140, 70, 70)
#         self.redUpper = (179, 255, 255)
#         self.greenLower = (30, 86, 46)
#         self.greenUpper = (100, 255, 255)
#         self.blueLower = (40, 50, 80)
#         self.blueUpper = (130, 255, 255)
#         self.q = queue.Queue()
#         super().__init__(self)
#         writefile(self.logfile,"Done.\n")
#     def camswitch(self):
#         self.index = int(not self.index)
#         cam_backends=[cv2.CAP_DSHOW,cv2.CAP_V4L2] #Linux and Windows camera backends
#         # NOTE: multiply the self.index by 2 when on the Pi
#         self.cam = cv2.VideoCapture(self.index*self.index_factor,cam_backends[int(platform=='linux')])            
#         self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1917) # Divides evenly by 9
#         self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  
#     # NOTE: This function is still unused because I don't quite know how to use
#     # it. I'll have to ask yinhuo for help with integrating this into the design.
#     def detect_shape(self,c):
#         shape = "empty"
#         peri = cv2.arcLength(c, True)
#         approx = cv2.approxPolyDP(c, 0.04 * peri, True)
#         # Triangle
#         if len(approx) == 3:
#             shape = "triangle"
#         # Square or rectangle
#         elif len(approx) == 4:
#             (x, y, w, h) = cv2.boundingRect(approx)
#             ar = w / float(h)
#         # A square will have an aspect ratio that is approximately
#         # equal to one, otherwise, the shape is a rectangle
#             shape = "rectangle"
#         # Pentagon
#         elif len(approx) == 5:
#             shape = "pentagon"
#         # Otherwise assume as circle or oval
#         else:
#             (x, y, w, h) = cv2.boundingRect(approx)
#             shape = "circle"
#         return shape
#     # Tell the camera thread to end smoothly, and raise a KeyboardInterupt
#     # that will be caught in the 'main_fetching' function in main.py
#     def destroy(self):
#         print("\nHalting program...")
#         writefile(self.logfile,"\nHalting program...  ")
#         if platform=='linux':
#             signal.signal(signal.SIGALRM, teardown_timeout_handler)
#             signal.alarm(2)
#         self.cam.release()
#         if self.demo:
#             cv2.destroyAllWindows()
#         if platform=='linux':
#             signal.alarm(0)
#         writefile(self.logfile,'\nDone.\nRaising KeyboardInterrupt to end the process...\n')
#         raise KeyboardInterrupt
#     def track(self,frame,goal):   
#         center = None
#         blurred = cv2.GaussianBlur(frame, (11,11), 0)
#         hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
#         if goal[:4]=='ball':
#             mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
#         elif goal=='user':
#             mask = cv2.inRange(hsv, self.redLower, self.redUpper)
#         elif goal=='waitpoint':
#             mask = cv2.inRange(hsv, self.blueLower, self.blueUpper)
#         mask = cv2.erode(mask, None, iterations=2)
#         mask = cv2.dilate(mask, None, iterations=2)
#         cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,\
#                                 cv2.CHAIN_APPROX_SIMPLE)
#         cnts = imutils.grab_contours(cnts)
#         if len(cnts) > 0:
#             c = max(cnts, key=cv2.contourArea)
#             ((x,y), radius) = cv2.minEnclosingCircle(c)
#             M = cv2.moments(c)
#             center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
#             if radius > 3:
#                 cv2.circle(frame, (int(x), int(y)), int(radius),\
#                         (0, 255, 255), 2)
#                 cv2.circle(frame, center, 5, (0,0,255), -1)
#         return center
#     def getimage(self,goal):
#         center = None
#         image=None
#         while True:
#             ret,image=self.cam.read()
#             if ret:
#                 center = self.track(image,goal)
#                 break
#         return center,image
#     # Draw the lines showing the 18 regions of the image. If the goal is in a region,
#     # then outline the region in green. Otherwise, outline it in red.
#     def show_tracking(self,image,position_xy):
#         if image is not None:
#             # Draw lines to show the regions of the screen
#             cv2.namedWindow("Camera",cv2.WINDOW_FREERATIO)
#             height, width = image.shape[:2]
#             for i in range(1,9):
#                 cv2.line(image, (i*(width//9), 0), (i*(width//9), height), (0, 0, 255), 2)
#             cv2.line(image, (0, height//2), (width, height//2), (0, 0, 255), 2)
#             if position_xy is not None:
#                 block_index = map_to_block_index(position_xy,image.shape)
#                 if block_index<18:
#                     region_map = {}
#                     for r in range(9):
#                         region_map[r]  = (r*(width//9),0)
#                         region_map[r+9]= (r*(width//9),height//2)
#                     top_left = region_map[block_index]
#                     bottom_right = (top_left[0]+width//9,top_left[1]+height//2)
#                     cv2.rectangle(image,top_left,bottom_right,(0,255,0),2)
#                 else:
#                     print(f"\nUnexpected position value: map_to_block_index({position_xy}) -> {block_index}\n")
#             # show the frame to our screen
#             cv2.imshow("Camera", image)
#             key = cv2.waitKey(1) & 0xFF
#             # if the 'x' key is pressed, stop the loop
#             if self.manual==0:
#                 if key == ord("x"):
#                     self.destroy()
#                 elif self.demo==1:
#                     if key == ord('m'):
#                         kill(getpid(),signal.SIGQUIT)
#                     elif key == ord('c') :
#                         self.camswitch()
#                     # elif key == ord('2') and platform=='linux':
#                     #     signal.raise_signal(signal.SIGUSR2)
#         return
    



# try:
#     def microcontroller_CTRL_ACK_handler(signum,frame): # SIGUSR1
#         signal.signal(signal.SIGUSR1,signal.SIG_IGN)
#         global ctrl 
#         if ctrl.gettimes is not None:
#             t1 = time.time()
#             time_data([ctrl.gettimes,ctrl.INT_start_time,t1],'fsm.get_state()',4)
#             ctrl.INT_start_time=0
#         ctrl.DONE = True
#         signal.signal(signal.SIGUSR1,microcontroller_CTRL_ACK_handler)
#     def microcontroller_PROX_handler(signum,frame): # SIGUSR2
#         signal.signal(signal.SIGUSR2,signal.SIG_IGN)
#         global ctrl
#         ctrl.proximity = int(not ctrl.proximity)
#         print(ctrl.proximity,'\n')
#         signal.signal(signal.SIGUSR2,microcontroller_PROX_handler)
# except:
#     pass
# def control_switch_handler(signum,frame):
#     signal.alarm(0)
#     global ctrl
#     ctrl.control_switch()
# # Special function for testing the image processing code directly
# def iproc_main():
#     global ctrl
#     import time
#     try:
#         from gpio import control
#     except:
#         pass
#     from sys import argv
#     if len(argv[1:]) == 0:
#         args='ball'
#     else:
#         args=argv[1]
#     try:
#         cam = camera(                        noprint=0,demo=1,manual=1,init_time=0,logfile='cam-dot-py-logfile')
#         try:
#             ctrl = control(    gettimes=None,noprint=0,demo=1,manual=1,init_time=0,logfile='cam-dot-py-logfile') 
#             signal.signal(signal.SIGUSR1, microcontroller_CTRL_ACK_handler)
#             signal.signal(signal.SIGUSR2, microcontroller_PROX_handler)
#             ctrl.init_manual_control(cam)
#             # 'ctrl' will be in the main loop of the manual control mode until it is escaped with CTRL+C,
#             # after which we will no longer be in manual control mode
#             ctrl.manual=0
#         except:
#             print("You're not on Linux, or an unexpected exception occurred in iproc_main() while initializing 'control'")
#         cam.manual=0
#         while True:
#             t0 = time.perf_counter()
#             cam.update_goal_position(args,time.time())
#             cam.get_goal_regions()
#             if platform=='linux':
#                 print('\033[F\033[K' * 1, end = "")
#                 print(f"FPS: {1/(time.perf_counter()-t0):.2f}")
#     except KeyboardInterrupt:
#         writefile('cam-dot-py-logfile','Done.')
#         print("\nDone.\nTerminated by user input.")
#     except Exception as e:
#         cam.destroy() # Free the threads
#         try:
#             ctrl.stop_all()
#         except Exception as e2:
#             print("COULDN'T DESTROY CONTROL INTERFACE")
#             print(e2,'\n')
#         writefile('errfile',f"ERROR: {e}\n\n")
#         backtrace = traceback.format_exc()
#         writefile('errfile',backtrace + '\n')
#         return 0


# if __name__=='__main__':
#     iproc_main()
