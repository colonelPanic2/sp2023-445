import cv2

cam = cv2.VideoCapture(0)
#cam2 = cv2.VideoCapture(1)

#adjust resolution
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ret, image = cam.read()
#cv2.imshow('Imagetest',image)
    
cv2.imwrite('/home/pi/testc720.jpg', image)
cam.release()
#cv2.destroyAllWindows()


#read image
