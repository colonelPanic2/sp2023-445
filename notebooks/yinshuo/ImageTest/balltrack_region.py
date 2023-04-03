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

def detect_shape(c):
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
        shape = "square" if ar >= 0.95 and ar <= 1.05 else "rectangle"

    # Pentagon
    elif len(approx) == 5:
        shape = "pentagon"

    # Otherwise assume as circle or oval
    else:
        (x, y, w, h) = cv2.boundingRect(approx)
        
        shape = "circle"

    return shape
    
    
cam = cv2.VideoCapture(0)
#try 1920 1080
#original as 1280 720
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)



# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
#original: (29, 86, 6) and (64, 255, 255)
#use redLower = (160, 100, 100)
# redUpper = (179, 255, 255) for red
#use blueLower = (40, 45, 80)
# blueUpper = (121, 255, 255)
greenLower = (30, 86, 46)
greenUpper = (100, 255, 255)
#red and blue colorspace as well

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
	
	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	center = None
	#0 for not found
	region = 0
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		for c in cnts:
			shape = detect_shape(c)
			if shape == "circle" :
				((x, y), radius) = cv2.minEnclosingCircle(c)
				# only proceed if the radius meets a minimum size
				#original size as 10
				if radius > 3:
					M = cv2.moments(c)
					center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
					
					#top left
					if center[0] < 640 and center[1] < 540:
						region = 1
					#top middle
					if 639 < center[0] and center[0] < 1280 and center[1] < 540:
						region = 2
					#top right
					if 1279 < center[0] and center[0] < 1920 and center[1] < 540:
						region = 3
					#bottom left
					if center[0] < 640 and center[1] > 539:
						region = 4
					#bottom middle
					if 639 < center[0] and center[0] < 1280 and center[1] > 539:
						region = 5
					#bottom right
					if 1279 < center[0] and center[0] < 1920 and center[1] > 539:
						region = 6
						
	print("region is:", region)			
				
			
	# update the points queue
	
	
	#delete this for final project
	# loop over the set of tracked points
	
	key = cv2.waitKey(1) & 0xFF
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

cam.release()

# close all windows
cv2.destroyAllWindows()
