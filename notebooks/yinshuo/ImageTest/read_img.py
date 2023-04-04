import PIL
from numpy import asarray

# load and show an image with Pillow
from PIL import Image
# Open the image form working directory
image = Image.open('testimage.jpg')
# summarize some details about the image
data = asarray(image)
#print(image.format)
print(image.size)
#print(image.mode)
# show the image

#print(data[2550,1600])
