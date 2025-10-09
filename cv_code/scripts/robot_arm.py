from picamera2 import Picamera2, Preview
import numpy as np
import time
import cv2
import csv

picam2 = Picamera2()

camera_config = picam2.create_preview_configuration()#main={"size": (3280, 2464)})
picam2.configure(camera_config)
picam2.start_preview(Preview.QTGL)

picam2.start()

time.sleep(2)





'''
image = cv2.imread('/home/pi/Desktop/randy.jpg')
cv2.imshow('Camera', pic_array)
cv2.waitKey(0)
'''


num = 0
while True:
	num+=1
	user_input = input('Press Enter to take source picture: ')
	
	if user_input == 'q':
		break
	image = picam2.capture_image()
	#img_arr = image.array
	'''image.save('capture_image.jpg')'''
	image = picam2.capture_array()
	'''image = cv2.imread(f'/home/pi/Desktop/chess_captures/capture_{num}.jpg')'''
	#image = cv2.imread(f'capture_image.jpg')
	
	'''lwr = np.array([0,0,143])
	upr = np.array([179,61,252])
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	msk = cv2.inRange(hsv, lwr, upr)
	
	krn = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 30))
	dlt = cv2.dilate(msk, krn, iterations=5)
	res = 255 - cv2.bitwise_and(dlt, msk)
	
	res = np.uint8(res)'''
	
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	mask_green = cv2.inRange(hsv, (25, 50, 90), (80, 255, 255))
	imask_green = mask_green>0
	green = np.full(image.shape, (255, 255, 255, 255), dtype=np.uint8)
	green[imask_green] = (0, 0, 0, 255)
	
	blurred = cv2.GaussianBlur(green, (9,9), 2)
	
	#gray = cv2.cvtColor(image , cv2.COLOR_BGR2GRAY)
	#print(gray.itemsize)
	#print(gray.shape)
	#cv2.imshow('bruh',image)
	#cv2.imshow('graybruh', gray)
	cv2.imwrite('image.jpg', image)
	cv2.imwrite('green.jpg', green)
	cv2.imwrite('blurred.jpg', blurred)
	
	#cv2.imwrite('gray.jpg', gray)
	
	#ret, corners = cv2.findChessboardCorners(gray, (3,3), cv2.CALIB_CB_ADAPTIVE_THRESH)
	#ret, corners = cv2.findCirclesGrid(green, (3,3), None, flags=cv2.CALIB_CB_SYMMETRIC_GRID)
	grid_dim = (4,4)
	ret, corners = cv2.findCirclesGrid(blurred, grid_dim, None, flags=cv2.CALIB_CB_SYMMETRIC_GRID)
	
	print(ret, corners)
	
	if ret:
		img = cv2.drawChessboardCorners(image, grid_dim, corners, ret)
		corners = corners.reshape((*grid_dim, 2))
		print(corners)
		for row in corners:
			for x, y in row:
				print(x, y, end=',  ')
			print()
		cv2.imshow('board', img)
		cv2.imwrite('circles.jpg', img)
		#cv2.waitKey(0)
		#cv2.destroyAllWindows()
		squares_filled = np.full(corners.shape[:2], False)
		print(squares_filled)
	
		while input("Press Enter ('c' to take new source image):") != 'c':
			covered_image = picam2.capture_array()
			new_image = cv2.imread("../images/chess_game_sequence/one_color/start_position.png")
			hsv_pixels = cv2.cvtColor(np.array([[new_image[int(x)][int(y)] for y, x in row] for row in corners]), cv2.COLOR_BGR2HSV)
			mask_green = cv2.inRange(hsv_pixels, (25, 50, 90), (80, 255, 255))
			print(mask_green)
			'''for i in range(len(corners)):
				for j in range(len(corners[i])):
					y, x = (int(_) for _ in corners[i][j])
					print(covered_image[x][y])'''
	'''
	blurred = cv2.GaussianBlur(green, (9, 9), 2)
	
	circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20)
	if circles is not None:
		circles = np.round(circles[0, :]).astype("int")
		for (x, y, r) in circles:
			cv2.circle(image, (x, y), r, (255, 0, 0), 4)
			cv2.rectange(image, (x-5, y-5), (x+5, y+5), (255, 0, 255), -1)
		
		cv2.imshow('board', image)
		cv2.imwrite('circles.jpg', image)
		cv2.waitKey(0)
		cv2.destroyAllWindows()
		'''
	'''img=rescaleFrame(img)'''
	
	'''pic_array = picam2.capture_array()
	print(pic_array.shape)
	with open(f'/home/pi/Desktop/chess_captures/pic_array_{num}.csv','w+') as f:
		writer = csv.writer(f)
		writer.writerows(pic_array)
	print(pic_array)'''
	'''picam2.stop()'''

	
picam2.stop()
