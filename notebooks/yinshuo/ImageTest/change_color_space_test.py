#https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html
#lower resolution!!!
import cv2 as cv
import numpy as np
cap = cv.VideoCapture(0)
while(1):
    # Take each frame
    _, frame = cap.read()
    # Convert BGR to HSV
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    # define range of blue color in HSV
    greenLower = np.array([29, 86, 6])
    greenUpper = np.array([64, 255, 255])
    # Threshold the HSV image to get only blue colors
    mask = cv.inRange(hsv, greenLower, greenUpper)
    # Bitwise-AND mask and original image
    res = cv.bitwise_and(frame,frame, mask= mask)
    cv.imshow('frame',frame)
    cv.imshow('mask',mask)
    cv.imshow('res',res)
    k = cv.waitKey(5) & 0xFF
    if k == 27:
        break
cv.destroyAllWindows()
