import cv2
from numpy import asarray

img= cv2.imread('roomlight.jpg')


data = asarray(img)

pos_x_up = img.shape[0]
pos_y_up = 0
pos_x_left = 0
pos_y_left = img.shape[1]
pos_x_right = 0
pos_y_right = 0
pos_x_down = 0
pos_y_down = 0

for i in range(img.shape[0]):
	#x for shape0
	#y for shape1
	
	for j in range(img.shape[1]):
		r = data[i, j, 0]
		g = data[i, j, 1]
		b = data[i, j, 2]
		
		#black filter
		if g < 30 or b < 30:
			continue
			
		if r < b * 0.6 and r > b * 0.5:
			if g < b * 1.05 and g > b * 0.95:
				if pos_x_up > i:
					pos_x_up = i
					pos_y_up = j
					
				if pos_x_down < i:
					pos_x_down = i
					pos_y_down = j
					
				if pos_y_left > j:
					pos_x_left = i
					pos_y_left = j
					
				if pos_y_right < j:
					pos_x_right = i
					pos_y_right = j

print(pos_x_up)
print(pos_y_up)
print(pos_x_left)
print(pos_y_left)
print(pos_x_right)
print(pos_y_right)
print(pos_x_down)
print(pos_y_down)
center_x = int((pos_x_down + pos_x_left + pos_x_right + pos_x_up) / 4)
center_y = int((pos_y_down + pos_y_left + pos_y_right + pos_y_up) / 4)
print("center is:")
print(center_x, center_y)
print(data[center_x, center_y])


