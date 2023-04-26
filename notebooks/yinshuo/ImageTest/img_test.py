import cv2

#cam = cv2.VideoCapture(0)
#cam.set(cv2.CAP_PROP_AUTO_WB, 1.0)

cam2 = cv2.VideoCapture(2)
cam2.set(cv2.CAP_PROP_AUTO_WB, 1.0)

#cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
#cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

cam2.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam2.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#       key value
#cam.set(3 , 640  ) # width        
#cam.set(4 , 480  ) # height       
#cam.set(10, 120  ) # brightness     min: 0   , max: 255 , increment:1  
#cam.set(11, 50   ) # contrast       min: 0   , max: 255 , increment:1     
#cam.set(12, 70   ) # saturation     min: 0   , max: 255 , increment:1
#cam.set(13, 13   ) # hue         
cam2.set(14, 5000   ) # gain           min: 0   , max: 127 , increment:1
#cam.set(15, -3   ) # exposure       min: -7  , max: -1  , increment:1
#cam.set(17, 5000 ) # white_balance  min: 4000, max: 7000, increment:1
#cam.set(28, 0    ) # focus          min: 0   , max: 255 , increment:5

while True:
    ret, image = cam2.read()
    #ret, image = cam.read()
    cv2.imshow('Imagetest',image)
    k = cv2.waitKey(1)
    if k != -1:
        break
#cv2.imwrite('/home/pi/testimagec720.jpg', image)
cv2.imwrite('/home/yf/Documents/ImageTest/testimagec720.jpg', image)
#cv2.imwrite('/home/yf/Documents/ImageTest/testimagefx30.jpg', image)
cam.release()
cv2.destroyAllWindows()
