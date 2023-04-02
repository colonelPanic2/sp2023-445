import cv2

cam = cv2.VideoCapture(0)
cam2 = cv2.VideoCapture(1)

#adjust resolution
#cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
#cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ret, image = cam.grab()
#cv2.imshow('Imagetest',image)
ret2, image2 = cam2.grab()
    
cv2.imwrite('/home/pi/two_camera1.jpg', image)
cv2.imwrite('/home/pi/two_camera2.jpg', image2)
cam.release()
cam2.release()
