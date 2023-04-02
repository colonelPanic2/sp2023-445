import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
#try not read grayscale
#img = cv.imread('object.jpg', cv.IMREAD_GRAYSCALE)
img = cv.imread('object.jpg')
assert img is not None, "file could not be read, check with os.path.exists()"
#original 100 and 200
#tried 50 and 200
#try 50 and 100
edges = cv.Canny(img,50,80)
plt.subplot(121),plt.imshow(img)
plt.title('Original Image'), plt.xticks([]), plt.yticks([])
plt.subplot(122),plt.imshow(edges)
plt.title('Edge Image'), plt.xticks([]), plt.yticks([])
plt.show()
