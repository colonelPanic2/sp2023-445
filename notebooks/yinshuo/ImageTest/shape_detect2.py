import cv2

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
        ar = w / float(h)
        shape = "circle" if ar >= 0.95 and ar <= 1.05 else "oval"

    return shape

image = cv2.imread('object1.jpg')

#canny edge

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.Canny(image,50,100)
#thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,51,7)
#ret, thresh = cv2.threshold(gray, 63, 150, 0)
cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
print(len(cnts))
cnts = cnts[0] if len(cnts) == 2 else cnts[1]
for c in cnts:
	area = cv2.contourArea(c)

	# only proceed if the radius meets a minimum size
	#original size as 10
	if area > 200:
		shape = detect_shape(c)
		x,y,w,h = cv2.boundingRect(c)
		cv2.putText(image, shape, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
	else:
		continue

cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
cv2.imshow('thresh', thresh)
cv2.imshow('image', image)
key = cv2.waitKey()
# if the 'q' key is pressed, stop the loop
#if key == ord("q"):

cv2.destroyAllWindows()

