from picamera2 import Picamera2, Preview
import cv2, numpy

picam2 = Picamera2()
sensor_width, sensor_height = picam2.camera_properties["PixelArraySize"]
picam2.set_controls({"ScalerCrop":(0,0,sensor_width, sensor_height)})
picam2.preview_size = (3280, 2464)
#picam2.preview_size = (5000, 4000)

#camera_config = picam2.create_preview_configuration()#main={"size": (1640, 1232)}) orginal code uses preview, we are testing still to see if we can capture images in BGR
camera_config = picam2.create_still_configuration()
camera_config["main"]["format"] = "BGR888"

picam2.configure(camera_config)
#picam2.start_preview(Preview.QTGL)
picam2.start()

image = picam2.capture_image()
image = picam2.capture_array()#[:, :, :3] - here originally

bgr_image = image.copy()  # copy to draw on
bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
#print(image) 

img = bgr_image
detector = cv2.QRCodeDetector()

retval, points = detector.detect(img)

if retval:
	for quad in points:
		quad.astype(int)
		
		for i in range(4):
			pt1 = tuple(quad[i])
			pt2 = tuple(quad[(i+1) % 4])
			#cv2.line(img, pt1, pt2, (0,255,0),2)
		
		print("Detected quad:", quad)
		
			

cv2.imshow('Detected Circles', bgr_image)

cv2.waitKey(0)
print("3")
cv2.destroyAllWindows()
