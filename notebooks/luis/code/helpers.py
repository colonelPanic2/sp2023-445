import subprocess,cv2,time,threading,signal,sys
import torch,argparse,imutils
from queue import Queue
from collections import deque
from imutils.video import VideoStream
import matplotlib.pyplot as plt
import numpy as np
# functions to run yinshuo's image processing code
# def ball_detect():
#     subprocess.run(['python3','yinshuo_img_proc/ball_detect.py'],shell=True)
# My functions 
def ls(dir=None):
    if dir==None:
        dirs = str(subprocess.check_output(["ls"]))[2:-1].split("\\n")[:-1]
    else:
        dirs = str(subprocess.check_output(["ls",dir]))[2:-1].split("\\n")[:-1]
    return dirs
def pytorch_scan(img):
    img = torch.from_numpy(img)
    R,G,B = torch.transpose(img,-3,-1).transpose(1,2).reshape((3,-1))
    t0 = time.perf_counter()
    # Check for 'r<b*0.6 and r>b*0.5' for each pair of R,B values from the same pixel
    R_filtered = torch.where((R>B*0.5) & (R<B*0.6),R,0)
    # Check for 'g<b*1.05 and g>b*0.95' for each pair of G,B values from the same pixel
    G = torch.where((G>B*0.95) & (G<B*1.05), G,0)
    # filter out black/white pixels
    GB_filtered = torch.where((G>=30) & (G<=245) & (B>=30) & (B<=245), 1,0)
    filtered = R_filtered*GB_filtered
    # If the number of nonzero values in 'filtered' is above some minimum threshold value, 
    # then there is a ball in the frame
    n_pixels = 0
    result = torch.count_nonzero(filtered!=0)>torch.tensor(n_pixels)# and torch.count_nonzero(G_filtered!=0)>torch.tensor(n_pixels)
    # print(f"Runtime (seconds): {time.perf_counter()-t0:0.4f}     Result: {result}")
    return (result,img)
# Handles all operations/data involving the camera
class Camera:
    def __init__(self):
        self.child_thread_id=None
        signal.signal(signal.SIGINT, self.signal_handler)
        print("\nInitializing camera...")
        self.cam = cv2.VideoCapture(0)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.frame_queue = Queue()
        # construct the argument parse and parse the arguments
        if len(sys.argv)==1:
            self.ap = argparse.ArgumentParser()
            self.ap.add_argument("-v", "--video",
                help="path to the (optional) video file")
            self.ap.add_argument("-b", "--buffer", type=int, default=64,
                help="max buffer size")
            self.args = vars(self.ap.parse_args())
            # define the lower and upper boundaries of the "green"
            # ball in the HSV color space, then initialize the
            # list of tracked points
            self.greenLower = (29, 86, 6)
            self.greenUpper = (64, 255, 255)
            self.pts = deque(maxlen=self.args["buffer"])
        self.capture_t = threading.Thread(target=self.capture_thread)
        self.image_count=0
        self.grayscale = False
        self.read_thread = False
        self.main_thread_id = threading.current_thread().ident
        # self.lock = threading.Lock()
        print("Done.")
    def start_capture(self):
        self.camera = cv2.VideoCapture(0)
        self.read_thread = True
        self.capture_t = threading.Thread(target=self.capture_thread)
        self.capture_t.start()
    def stop_capture(self):
        self.read_thread = False
        self.capture_t.join()
        self.camera.release()
    # NOTE: The signal handler for KeyboardInterrupts is incomplete
    def signal_handler(self,signum,frame):
        global sigint
        sigint = True
        if self.child_thread_id!=threading.current_thread().ident:
            # self.lock.acquire()
            # if self.child_thread_id!=threading.current_thread().ident:
            print("\nHalting process...")
            if int(sys.argv[1])>1: 
                print(self.main_thread_id==threading.current_thread().ident)
                cv2.destroyAllWindows()
                # This has a chance of hanging/crashing
                self.stop_capture()
            print("Done.")
            # self.lock.release()
            exit(0)
            # else:
            #     self.lock.acquire()
            #     print("\nNotifying the main thread...")
            #     time.sleep(2)
            #     self.lock.release()
        else:
            # self.lock.acquire()
            print("\nNotifying the main thread...")
            time.sleep(2)
            # self.lock.release()
            # print("Done.")
    def capture_thread(self):
        global sigint
        sigint = False
        self.child_thread_id = threading.current_thread().ident
        if self.grayscale==False:
            while self.read_thread==True:
                ret,frame =self.cam.read()
                if ret:
                    self.frame_queue.put(frame)
        else:
            while self.read_thread==True:
                ret,frame = self.cam.read()
                if ret:
                    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                    self.frame_queue.put(gray)

    def getimages(self,time_s=5):
        print(f"\nGathering samples from the camera for {time_s} seconds\nand storing as png images in the 'testimg' directory.")
        self.start_capture()
        dirs = ls()
        if 'testimg' not in dirs:
            subprocess.run("mkdir testimg",shell=True)
        t_init = time.perf_counter()
        while time.perf_counter()-t_init<time_s:
            if not self.frame_queue.empty():
                image = self.frame_queue.get() 
                cv2.imwrite('testimg/test{}.png'.format(self.image_count), image)
                self.image_count += 1
        self.stop_capture()
    def detect(self,filename,dir=''):
        tic = time.perf_counter()
        img = cv2.imread(dir+filename)
        # print(filename+":")
        result = pytorch_scan(img)
        #note: go from below to top is generally faster
        x,y,pval = 0,0,img[0,0]
        for i in range(img.shape[0])[::-1]:
            # i = img.shape[0] - a - 1
            #break flag
            flag = False
            for j in range(img.shape[1]):
                r = img[i, j, 0]
                g = img[i, j, 1]
                b = img[i, j, 2]
                #black filter
                if g < 30 or b < 30:
                    continue
                #white filter
                if g > 245 or b > 245:
                    continue
                #if r < g * 0.6 and r > g * 0.4:
                if r<b*0.6 and r>b*0.5:
                    if g<b*1.05 and g>b*0.95:
                        x,y,pval = i,j,img[i,j]
                        flag = True
                        break
            if flag == True:
                break
        toc = time.perf_counter()
        # print(f"Runtime (seconds): {toc- tic:0.4f}     Result: {flag}")			
        # print("{}: {}".format(filename,flag))
        # if flag==True:
        #     print(x,y,pval)
        return (result[0],flag,img,result[1])
    def balltrack(self):
        global sigint
        sigint = False
        # print("Main thread: {}".format(threading.current_thread().ident))
        self.start_capture()
        # keep looping
        while True:
            if not self.frame_queue.empty():
                # grab the current frame
                frame = self.frame_queue.get() 
                # cv2.imshow('Frame',frame)
                # resize the frame, blur it, and convert it to the HSV
                # color space
                # original 600
                frame = imutils.resize(frame, width=300)
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
                    c = max(cnts, key=cv2.contourArea)
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    # only proceed if the radius meets a minimum size
                    if radius > 10:
                        # draw the circle and centroid on the frame,
                        # then update the list of tracked points
                        cv2.circle(frame, (int(x), int(y)), int(radius),
                            (0, 255, 255), 2)
                        cv2.circle(frame, center, 5, (0, 0, 255), -1)
                # update the points queue
                self.pts.appendleft(center)
                # loop over the set of tracked points
                for i in range(1, len(self.pts)):
                    # if either of the tracked points are None, ignore
                    # them
                    if self.pts[i - 1] is None or self.pts[i] is None:
                        continue
                    # otherwise, compute the thickness of the line and
                    # draw the connecting lines
                    thickness = int(np.sqrt(self.args["buffer"] / float(i + 1)) * 2.5)
                    cv2.line(frame, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)
                # show the frame to our screen
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF
                # # if the 'q' key is pressed, stop the loop
                if key == ord("q"):
                    break
        self.stop_capture()
    def edge_detect(self):
        self.grayscale = True
        self.start_capture()
        while True:
            if not self.frame_queue.empty():
                img = self.frame_queue.get()
                edges = cv2.Canny(img,100,200)
                cv2.imshow("Frame", edges)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
        self.stop_capture()

def main(process,time_s):
    cam = Camera()
    ### cam.getimages() and cam.detect() TEST
    if process==0:
        if sys.platform=='win32':
            subprocess.run('rm -r testimg',shell=True)
        else: # If we're not on windows, we're on Linux
            subprocess.run('rm -rf testimg',shell=True)
        cam.getimages(time_s)
        print(f"\nRunning ball detection algorithm on {cam.image_count} image samples.\n")
        discrepancies = 0
        for i in range(cam.image_count):
            results = cam.detect("test{}.png".format(i),dir='testimg/')
            if results[0]!=results[1]:
                discrepancies+=1
                print(f"test{i}.png")
                cv2.imwrite(f"test{i}.png",results[2])
                cv2.imwrite(f"test{i}_{results[0]}_{results[1]}_{discrepancies}.png",results[3].numpy())
    ### cam.detect() TEST (unit test)
    elif process==1:
        dirs = ls()
        discrepancies=0
        for file in dirs:
            if len(file)>4 and file[-4:]=='.png' and '_' not in file:
                results = cam.detect(file)
                if results[0]!=results[1]:
                    discrepancies+=1
                    print(file)
                    # print(np.where(results[2]!=results[3].numpy()))
                    # cv2.imwrite(file[:-4]+"_diff.png",results[2])
    ### cam.balltrack() TEST
    elif process==2:
        cam.balltrack()
    ### cam.edge_detect() TEST
    elif process==3:
        cam.edge_detect()

if __name__=='__main__':
    time_s=None
    if sys.argv[1]=='2':
        print("Cannot execute 'balltrack' with command line arguments.")
    else:
        if len(sys.argv)>1:
            
            process=int(sys.argv[1])
            if process==0 and len(sys.argv)==3:
                time_s = float(sys.argv[2])
            elif process==0:
                time_s = 1
        else:
            process = 2 # Manually choose the process (edge_detect requires no extra args)
        main(process,time_s)
### Sanity check: example of working torch transformation
###                   R,G,B
# t = torch.tensor([\
#                   [[1,2,3],\
#                    [4,5,6]],\
#                   [[7,8,9],\
#                    [10,11,12]]\
#                  ])
# print(torch.transpose(t,-3,-1).transpose(1,2).reshape((3,-1)))