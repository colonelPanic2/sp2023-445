import cv2
#from numpy import asarray
#color detection
#performance optimiza
import time
tic = time.perf_counter()
img = cv2.imread('carwheel.jpg')

#print(img.shape)
#data = asarray(img)
#print(data.shape)

#note: go from bellow to top is generally faster

#for i in range(img.shape[0]):
for a in range(img.shape[0]):
	i = img.shape[0] - a - 1
	#break flag
	flag = False
	for j in range(img.shape[1]):
		r = img[i, j, 0]
		g = img[i, j, 1]
		b = img[i, j, 2]
		
		#black filter
		if g < 30 or b < 30:
			continue
		#white filter
		if g > 245 or b > 245:
			continue
		
		#if r < g * 0.6 and r > g * 0.4:
		if r < b * 0.6 and r > b * 0.5:
			if g < b * 1.05 and g > b * 0.95:
				print(i, j)
				print(img[i,j])
				print("true")
				flag = True
				break
	if flag == True:
		break
toc = time.perf_counter()
print(f"Time is :{toc- tic:0.4f} second")			
print("false")
	

