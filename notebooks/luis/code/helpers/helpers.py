import subprocess,time,signal,sys,shlex,os
from timedata.plots import process_data
import numpy as np
platform=sys.platform
# Class for remote testing of the manual controls. Mimics
# the behavior of the RPi.GPIO library functions. Don't
# try to implement any of these functions. They are only
# placeholders for the actual versions that we will be 
# using from the RPi.GPIO library.
class remote_gpio:
    def __init__(self,pins=[17,27,12,13,4,25,5,6,16,26,18,24, 20,21]):
        self.pins=pins
        self.pinout={}
        self.OUT = 'OUT'
        self.BCM = 'BCM'
        self.BOARD = 'BOARD' # *****
        self.mode = None
        self.warnings=None
        # NOTE: UNTESTED MICROCONTROLLER COMMS CODE
        self.IN = 'IN'
        self.PUD_DOWN = 'PUD_DOWN'
        self.PUD_UP = 'PUD_UP'
        self.RISING = 'STANDING HEEEEEEERE I REALIIIIIIIIIZE YOU WERE JUST LIKE ME TRYING TO MAKE HISTORYYYYYYYYY~'
        return
    def setmode(self,mode):
        self.mode=mode
    def setwarnings(self,val):
        self.warnings=val
    def setup(self,pin,direction,pull_up_down=None):
        self.pinout[pin]=0
        return
    def output(self,pin,val):
        self.pinout[pin]=val
    def input(self,pin):
        return self.pinout[pin]
    # NOTE: UNTESTED MICROCONTROLLER COMMS CODE
    def add_event_detect(self,pin,condition,callback=None,bouncetime=None):
        # This function should set up an event listener that runs the 'callback' function
        # when the given condition is met on the given pin.
        return
io = remote_gpio()
def decode_signal(signal):
    signal_map={'L':{'00':'LS','01':'LF','11':'LB',  '10':'CS0'},\
                'R':{'00':'RS','01':'RF','11':'RB',  '10':'CS1'},\
                'P':{'00':'PS','10':'PO','11':'PC',  '01':'CS2'}}
    return f"{signal_map['L'][signal[0:2]]}-{signal_map['R'][signal[2:4]]}-{signal_map['P'][signal[4:6]]} "
def teardown_timeout_handler(signum,frame):
    current_time = time.localtime()
    current_date = time.strftime("%Y-%m-%d", current_time)[5:]
    current_time = time.strftime("%Y-%m-%d_%H.%M.%S", current_time)[11:]
    # backtrace = traceback.format_exc()
    err_message = "ERROR: TIMEOUT IN 'camera.destroy()' WHILE TRYING TO RELEASE\nTHE CAMERA OR JOIN THE CAMERA THREAD WITH THE MAIN THREAD.\n\nAttempting processicide..."
    output = f"\n\n{current_time}\n{err_message}"
    writefile(f'logs/{current_date}/err.txt',output)
    print(f'{err_message}')
    os.kill(os.getpid(), signal.SIGKILL)
# Write the input string to the end of the file with the given name. 
def writefile(fname,content):
    dirs = ls()
    if 'init-err.txt' not in dirs:
        subprocess.run(shlex.split("touch init-err.txt"))
    with open(fname,'a') as f:
        f.write(content)
# Calculate the index corresponding to the region of the image with the given dimensions
# in which the pixel with the given column and row is located.
def map_to_block_index(col_row,dims=(1080,1920)):
    col_blocks = dims[1]//3
    row_blocks = dims[0]//2
    region_index = (col_row[0]//col_blocks) + 3*(col_row[1]>=row_blocks)
    return region_index
# 18 SEGMENTS
# # Calculate the index corresponding to the region of the image with the given dimensions
# # in which the pixel with the given column and row is located.
# def map_to_block_index(col_row,dims=(1080,1920)):
#     col_blocks = dims[1]//9
#     row_blocks = dims[0]//2
#     region_index = (col_row[0]//col_blocks) + 9*(col_row[1]>=row_blocks)
#     return region_index
# Get a list of all files/subdirectories in the passed in directory.
# *** Doesn't seem to work with '..' directory.
def ls(dir=None):
    if dir==None:
        dirs = str(subprocess.check_output(shlex.split(["dir","ls"][int(platform=='linux')])))[2:-1].split("\\n")[:-1]
    else:
        dirs = str(subprocess.check_output(shlex.split(["dir "+dir,"ls "+dir][int(platform=='linux')])))[2:-1].split("\\n")[:-1]
    return dirs
# Clear the terminal
def clear():
    clear_command = shlex.split(['cls','clear'][int(platform=='linux')])
    if platform=='linux':
        subprocess.run(clear_command)
    else:
        subprocess.run(clear_command,shell=True)
# Creates an error and a logging file. Returns the paths to each file as strings
# along withe the time of creation.
def logdata():
    current_time = time.localtime()
    current_date = time.strftime("%Y-%m-%d", current_time)[5:]
    current_time = time.strftime("%Y-%m-%d_%H.%M.%S", current_time)[11:]
    dirs = ls('logs')
    if current_date not in dirs:
        print(dirs)
        subprocess.run(shlex.split(f'mkdir logs/{current_date}'))
    logs = ls(f"logs/{current_date}")
    if f'{current_time}.txt' not in logs:
        subprocess.run(shlex.split(f"touch logs/{current_date}/{current_time}.txt"))
    if 'err.txt' not in logs:
        subprocess.run(shlex.split(f'touch logs/{current_date}/err.txt'))
    logfile = f"logs/{current_date}/{current_time}.txt"
    errfile = f"logs/{current_date}/err.txt"
    init_time = time.time()
    return (init_time,logfile,errfile)
# Keep track of the runtime data for the fetching subsystem. 
# (unusable with the current code)
def time_data(args,state,step,t0=0,noprint=0,logfile=None,num_samples=None):
    global T0_SET
    global T0
    global T1
    global no_print
    global log_file
    global time_data_dict
    global microcontroller_time_data_list
    global n_samples
    if args=='time':
        if step==0:
            T0_SET = 0
            T0 = 0
            T1 = 0
            time_data_dict={'WAIT':[],'CHASE':[],'ACQUIRE':[],'FETCH':[],'RETURN':[]}
            microcontroller_time_data_list=[]
            no_print=noprint
            log_file = logfile
            n_samples = num_samples
        elif step==1:
            T0_SET = 0
        elif step==2:
            T1 = time.perf_counter()
            if T0_SET==1:
                time_data_dict[state].append(round(1000*(T1-T0),2))
            T0=time.perf_counter()
            T0_SET = 1
            if n_samples is not None and len(time_data_dict[state])>n_samples:
                return -13
        elif step==3:
            for state,runtimes in list(time_data_dict.items()):
                # TODO: ENCOUNTERED AN ERROR IN WHICH THE FIRST ENTRY IN THE TIMEDATA
                # IS OFTEN DISPROPORTIONATELY LARGER THAN THE REST OF THE RUNTIME
                # DATA. THE MODIFICATIONS BELOW ARE AN ATTEMPT AT A TEMPORARY SOLUTION
                if len(runtimes)==1:
                    runtimes=[]
                elif len(runtimes)>1:
                    runtimes=runtimes[1:]
                time_data_dict[state] = (round(np.mean(np.array(runtimes)),2),len(time_data_dict[state])-int(len(time_data_dict[state])>1))
            return time_data_dict
        elif step==5:
            return microcontroller_time_data_list
        # NOTE: UNTESTED MICROCONTROLLER COMMS CODE
    elif step == 4 and args[0] is not None and str(args[0])=='time' and args[1]!=0:
        _, INT_start_time, INT_end_time = args
        microcontroller_time_data_list.append(round((INT_end_time-INT_start_time)*1000,2))
        if not no_print and microcontroller_time_data_list[-1]>=200:
            writefile(log_file,f"{microcontroller_time_data_list[-1]}\n")

    return 0
# If we were collecting time data for a complete run of the program
# then write the data to the .csv file in the 'timedata' directory.
def timedata_files(gettimes,init_time):
    if gettimes is not None and gettimes=='time':
        dirs = ls()
        if "timedata" not in dirs:
            subprocess.run(shlex.split("mkdir timedata"))
        dirs = ls('timedata')
        if "timedata.csv" not in dirs:
            subprocess.run(shlex.split("touch timedata/timedata.csv"))
        time_data_dict                 = time_data(gettimes,'',3)
        print("\n -------- RUNTIME DATA ACQUIRED --------")
        for state,runtime_loopnum in list(time_data_dict.items()):
            if runtime_loopnum[1]==0:
                data_content_csv=f"{state},{0},{0}\n"
            else:
                data_content_csv=f"{state},{runtime_loopnum[1]},{runtime_loopnum[0]}\n"
            writefile('timedata/timedata.csv',data_content_csv)
        # number of times "main" was called, runtime of call to main
        writefile('timedata/timedata.csv',f"{1},{round(time.time()-init_time,2)}\n")
        microcontroller_time_data_list = time_data(gettimes,'',5)
        process_data(microcontroller_time_data_list)
# NOTE: All of the following code is outdated, but it still implements some features that 
# might be useful later. So I've decided to keep it even though it isn't in use right now.
# from queue import Queue
# from collections import deque
# from imutils.video import VideoStream
# import matplotlib.pyplot as plt
# class Camera:
#     def __init__(self):
#         self.child_thread_id=None
#         signal.signal(signal.SIGINT, self.signal_handler)
#         print("\nInitializing camera...")
#         self.cam = cv2.VideoCapture(0)
#         self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1281)
#         self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#         self.new_image = False
#         self.frame_queue = None#Queue()
#         # construct the argument parse and parse the arguments
#         if len(sys.argv)==1:
#             self.ap = argparse.ArgumentParser()
#             self.ap.add_argument("-v", "--video",
#                 help="path to the (optional) video file")
#             self.ap.add_argument("-b", "--buffer", type=int, default=64,
#                 help="max buffer size")
#             self.args = vars(self.ap.parse_args())
#             # define the lower and upper boundaries of the "green"
#             # ball in the HSV color space, then initialize the
#             # list of tracked points
#             self.greenLower = (29, 86, 6)
#             self.greenUpper = (64, 255, 255)
#             self.pts = deque(maxlen=self.args["buffer"])
#         self.capture_t = threading.Thread(target=self.capture_thread)
#         self.image_count=0
#         self.grayscale = False
#         self.read_thread = False
#         self.main_thread_id = threading.current_thread().ident
#         self.lock = threading.Lock()
#         print("Done.")
#     def start_capture(self):
#         self.read_thread = True
#         self.capture_t = threading.Thread(target=self.capture_thread)
#         self.capture_t.start()
#     def stop_capture(self):
#         self.read_thread = False
#         self.capture_t.join()
#     # NOTE: The signal handler for KeyboardInterrupts is incomplete
#     def signal_handler(self,signum,frame):
#         global sigint
#         sigint = True
#         if self.child_thread_id!=threading.current_thread().ident:
#             # self.lock.acquire()
#             # if self.child_thread_id!=threading.current_thread().ident:
#             print("\nHalting process...")
#             if int(sys.argv[1])>1: 
#                 print(self.main_thread_id==threading.current_thread().ident)
#                 cv2.destroyAllWindows()
#                 # This has a chance of hanging/crashing
#                 self.stop_capture()
#             print("Done.")
#             # self.lock.release()
#             exit(0)
#             # else:
#             #     self.lock.acquire()
#             #     print("\nNotifying the main thread...")
#             #     time.sleep(2)
#             #     self.lock.release()
#         else:
#             # self.lock.acquire()
#             print("\nNotifying the main thread...")
#             time.sleep(2)
#             # self.lock.release()
#             # print("Done.")
#     def capture_thread(self):
#         global sigint
#         sigint = False
#         global image
#         image = None
#         self.child_thread_id = threading.current_thread().ident
#         if self.grayscale==False:
#             while self.read_thread==True:
#                 ret,frame =self.cam.read()
#                 if ret:
#                     # self.frame_queue.put(frame)
#                     image = frame
#         else:
#             while self.read_thread==True:
#                 ret,frame = self.cam.read()
#                 if ret:
#                     image = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

#     def getimages(self,time_s=5):
#         global image
#         print(f"\nGathering samples from the camera for {time_s} seconds\nand storing as png images in the 'testimg' directory.")
#         self.start_capture()
#         dirs = ls()
#         if 'testimg' not in dirs:
#             subprocess.run("mkdir testimg",shell=True)
#         t_init = time.perf_counter()
#         while time.perf_counter()-t_init<time_s:
#             # if not self.frame_queue.empty():
#             if image is not None:
#                 frame = image 
#                 cv2.imwrite('testimg/test{}.png'.format(self.image_count), image)
#                 self.image_count += 1
#         self.stop_capture()
#     def detect(self,filename,dir=''):
#         tic = time.perf_counter()
#         img = cv2.imread(dir+filename)
#         # print(filename+":")
#         #note: go from below to top is generally faster
#         x,y,pval = 0,0,img[0,0]
#         for i in range(img.shape[0])[::-1]:
#             # i = img.shape[0] - a - 1
#             #break flag
#             flag = False
#             for j in range(img.shape[1]):
#                 r = img[i, j, 0]
#                 g = img[i, j, 1]
#                 b = img[i, j, 2]
#                 #black filter
#                 if g < 30 or b < 30:
#                     continue
#                 #white filter
#                 if g > 245 or b > 245:
#                     continue
#                 #if r < g * 0.6 and r > g * 0.4:
#                 if r<b*0.6 and r>b*0.5:
#                     if g<b*1.05 and g>b*0.95:
#                         x,y,pval = i,j,img[i,j]
#                         flag = True
#                         break
#             if flag == True:
#                 break
#         toc = time.perf_counter()
#         # print(f"Runtime (seconds): {toc- tic:0.4f}     Result: {flag}")			
#         # print("{}: {}".format(filename,flag))
#         # if flag==True:
#         #     print(x,y,pval)
#         return (flag,img)
#     def balltrack(self):
#         global sigint
#         sigint = False
#         # print("Main thread: {}".format(threading.current_thread().ident))
#         self.start_capture()
#         # keep looping
#         while True:
#             if not self.frame_queue.empty():
#                 # grab the current frame
#                 frame = self.frame_queue.get() 
#                 # cv2.imshow('Frame',frame)
#                 # resize the frame, blur it, and convert it to the HSV
#                 # color space
#                 # original 600
#                 frame = imutils.resize(frame, width=300)
#                 blurred = cv2.GaussianBlur(frame, (11, 11), 0)
#                 hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
#                 # construct a mask for the color "green", then perform
#                 # a series of dilations and erosions to remove any small
#                 # blobs left in the mask
#                 mask = cv2.inRange(hsv, self.greenLower, self.greenUpper)
#                 mask = cv2.erode(mask, None, iterations=2)
#                 mask = cv2.dilate(mask, None, iterations=2)
#                 # find contours in the mask and initialize the current
#                 # (x, y) center of the ball
#                 cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
#                     cv2.CHAIN_APPROX_SIMPLE)
#                 cnts = imutils.grab_contours(cnts)
#                 center = None
#                 # only proceed if at least one contour was found
#                 if len(cnts) > 0:
#                     # find the largest contour in the mask, then use
#                     # it to compute the minimum enclosing circle and
#                     # centroid
#                     c = max(cnts, key=cv2.contourArea)
#                     ((x, y), radius) = cv2.minEnclosingCircle(c)
#                     M = cv2.moments(c)
#                     center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
#                     # only proceed if the radius meets a minimum size
#                     if radius > 10:
#                         # draw the circle and centroid on the frame,
#                         # then update the list of tracked points
#                         cv2.circle(frame, (int(x), int(y)), int(radius),
#                             (0, 255, 255), 2)
#                         cv2.circle(frame, center, 5, (0, 0, 255), -1)
#                 # update the points queue
#                 self.pts.appendleft(center)
#                 # loop over the set of tracked points
#                 for i in range(1, len(self.pts)):
#                     # if either of the tracked points are None, ignore
#                     # them
#                     if self.pts[i - 1] is None or self.pts[i] is None:
#                         continue
#                     # otherwise, compute the thickness of the line and
#                     # draw the connecting lines
#                     thickness = int(np.sqrt(self.args["buffer"] / float(i + 1)) * 2.5)
#                     cv2.line(frame, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
#                 # show the frame to our screen
#                 cv2.imshow("Frame", frame)
#                 key = cv2.waitKey(1) & 0xFF
#                 # # if the 'q' key is pressed, stop the loop
#                 if key == ord("q"):
#                     break
#         self.stop_capture()
#     def edge_detect(self):
#         self.grayscale = True
#         self.start_capture()
#         while True:
#             if not self.frame_queue.empty():
#                 img = self.frame_queue.get()
#                 edges = cv2.Canny(img,100,200)
#                 cv2.imshow("Frame", edges)
#                 key = cv2.waitKey(1) & 0xFF
#                 if key == ord("q"):
#                     break
#         self.stop_capture()

# def main(process,time_s):
#     cam = Camera()
#     ### cam.getimages() and cam.detect() TEST
#     if process==0:
#         if sys.platform=='win32':
#             subprocess.run('rm -r testimg',shell=True)
#         else: # If we're not on windows, we're on Linux
#             subprocess.run('rm -rf testimg',shell=True)
#         cam.getimages(time_s)
#         print(f"\nRunning ball detection algorithm on {cam.image_count} image samples.\n")
#         discrepancies = 0
#         for i in range(cam.image_count):
#             results = cam.detect("test{}.png".format(i),dir='testimg/')
#             if results[0]!=results[1]:
#                 discrepancies+=1
#                 print(f"test{i}.png")
#                 cv2.imwrite(f"test{i}.png",results[2])
#                 cv2.imwrite(f"test{i}_{results[0]}_{results[1]}_{discrepancies}.png",results[3].numpy())
#     ### cam.detect() TEST (unit test)
#     elif process==1:
#         dirs = ls()
#         discrepancies=0
#         for file in dirs:
#             if len(file)>4 and file[-4:]=='.png' and '_' not in file:
#                 results = cam.detect(file)
#                 if results[0]!=results[1]:
#                     discrepancies+=1
#                     print(file)
#                     print(np.where(results[2]!=results[3].numpy()))
#                     cv2.imwrite(file[:-4]+"_diff.png",results[2])
#     ### cam.balltrack() TEST
#     elif process==2:
#         cam.balltrack()
#     ### cam.edge_detect() TEST
#     elif process==3:
#         cam.edge_detect()

# if __name__=='__main__':
#     time_s=None
#     if len(sys.argv)>1 and sys.argv[1]=='2':
#         print("Cannot execute 'balltrack' with command line arguments.")
#     else:
#         if len(sys.argv)>1:
            
#             process=int(sys.argv[1])
#             if process==0 and len(sys.argv)==3:
#                 time_s = float(sys.argv[2])
#             elif process==0:
#                 time_s = 1
#         else:
#             process = 2 # Manually choose the process (edge_detect requires no extra args)
#         main(process,time_s)
