#modify this and lower data rate!!!

#working! find ways to distinguish ball and envelop

#correct! do a color space transform and then shape detect!

#merge shape detect success
from collections import deque

import numpy as np
import argparse
import cv2
import imutils
import time
    
cam = cv2.VideoCapture(0)
#cam = cv2.VideoCapture(2)
#try 1920 1080
#original as 1280 720
cam.set(cv2.CAP_PROP_AUTO_WB, 1.0)
#cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
	help="path to the (optional) video file")
	#was 64
ap.add_argument("-b", "--buffer", type=int, default=32,
	help="max buffer size")
args = vars(ap.parse_args())

# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
#original: (29, 86, 6) and (64, 255, 255)
#use redLower = (160, 100, 100)
# redUpper = (179, 255, 255) for red
#use blueLower = (40, 45, 80)
# blueUpper = (121, 255, 255)
greenLower = (30, 86, 46)
greenUpper = (100, 255, 200)
#red and blue colorspace as well

pts = deque(maxlen=args["buffer"])
# allow the camera or video file to warm up
time.sleep(1.0)

# keep looping
while True:
	# grab the current frame
	ret, frame = cam.read()
	
	blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	
	#test
	#cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	#cnts = imutils.grab_contours(cnts)
	#was 100, change to 50
	#was 1.2, change to 2.0
	circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 4.0, 3)
	#if circles is None:
		#print("there is no ball")
	if circles is not None:
		#print("there is ball")
		circles = np.round(circles[0,:]).astype("int")
		#x and y is center
		for (x, y, r) in circles:
			# was 3
			if r < 3:
				continue
			
			cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 255), 2)
			cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
	# update the points queue
	
	
	#delete this for final project
	# loop over the set of tracked points
	for i in range(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
		if pts[i - 1] is None or pts[i] is None:
			continue
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
	# show the frame to our screen
	cv2.imshow("Frame", frame)
	
	key = cv2.waitKey(1) & 0xFF
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

cam.release()

# close all windows
cv2.destroyAllWindows()
