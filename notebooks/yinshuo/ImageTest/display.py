import cv2

#im = cv2.imread('sunlight.jpg')
im = cv2.imread('roomlight.jpg')

#im = cv2.resize(im, (960, 720))
img = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
# Open the image form working directory
print(img.shape)
while True:
    
    cv2.imshow('Imagetest',img)
    k = cv2.waitKey(1)
    if k != -1:
        break

cv2.destroyAllWindows()
                                                                            
