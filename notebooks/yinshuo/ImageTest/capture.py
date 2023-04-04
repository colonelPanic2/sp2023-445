import cv2

cam = cv2.VideoCapture(0)
#cam2 = cv2.VideoCapture(1)

#adjust resolution
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

ret, image = cam.read()
#cv2.imshow('Imagetest',image)
    
cv2.imwrite('/home/pi/sp2023-445/notebooks/yinshuo/ImageTest/ball2meter.jpg', image)
cam.release()
#cv2.destroyAllWindows()


#read image
