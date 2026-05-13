import csv
import math
import numpy as np
import time
from bisect import bisect
import os
from PIL import Image

os.environ.update({
    "PNG_IGNORE_WARNINGS": "1",
    "QT_QPA_PLATFORM_PLUGIN_PATH": "/home/raspberrypi/Documents/robot_arm/venv/lib/python3.11/site-packages/cv2/qt/plugins/platforms"
})

from picamera2 import Picamera2, Preview
import cv2

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

#picam2.close()
# Setting chessboard grid dimension
grid_dimension = (8,8) #original = (8,2)
# Experiment with thresholds once we have real pictures
# Saturation of lower bound might need to be increased
color_threshold_lower = (0, 100, 0)
color_threshold_upper= (255, 255, 255)

#BGR
black = (0, 0, 0)
white = (255, 255, 255)
blue = (255, 0, 0)
green = (73, 246, 122)
red = (49, 49, 255)
pink = (196, 102, 255)
orange = (77, 145, 255)
yellow = (40, 255, 255)

#RGB
'''black = (0, 0, 0)
white = (255, 255, 255)
blue = (82, 113, 255)
green = (99, 191, 0)
red = (255, 49, 49)
pink = (255, 102, 196)
orange = (255, 145, 77)
yellow = (255, 222, 89)'''

rows = [1232 // 8 * i for i in range(8)]
cols = [1640 // 8 * i for i in range(8)]

def get_hue(rgb_color):
    rgb_array = np.uint8([[list(rgb_color)]])
    hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_BGR2HSV) #changed this from RGB2HSV
    hsv_color = tuple(hsv_array[0][0])
    return hsv_color[0]

#hues = (
#    (get_hue(blue), 'p'),
#    (get_hue(green), 'b'),
#    (get_hue(red), 'k'),
#    (get_hue(pink), 'n'),
#    (get_hue(orange), 'q'),
#    (get_hue(yellow), 'r')
#)
hues = (
    (get_hue(blue), 'b'),
    (get_hue(green), 'g'),
    (get_hue(red), 'r'),
    (get_hue(pink), 'p'),
    (get_hue(orange), 'o'),
    (get_hue(yellow), 'y')
)

piece_icon = {
    "K":u"♔",
    "Q":u"♕",
    "R":u"♖",
    "B":u"♗",
    "N":u"♘",
    "P":u"♙",
    "k":u"♚",
    "q":u"♛",
    "r":u"♜",
    "b":u"♝",
    "n":u"♞",
    "p":u"♟"
}

def hue_distance(h1, h2):
    diff = abs(int(h1) - int(h2))
    return min(diff, 180 - diff)

def sample_color(image, x, y, size=5):
    half = size // 2
    roi = image[max(0, y-half):y+half, max(0, x-half):x+half]
    mean = cv2.mean(roi)[:3]
    return tuple(map(int, mean))
    
def get_piece(image, circle):
    x, y, r = map(int, circle)

    # --- Create masks ---
    mask_outer = np.zeros(image.shape[:2], dtype=np.uint8)
    mask_inner = np.zeros(image.shape[:2], dtype=np.uint8)

    # Full circle mask
    cv2.circle(mask_outer, (x, y), r, 255, -1)
    # Inner (half-radius) mask
    cv2.circle(mask_inner, (x, y), int(r * 0.5), 255, -1)

    # Outer half mask (the ring area)
    outer_half_mask = cv2.subtract(mask_outer, mask_inner)

    # --- Sample BGR color in outer ring ---
    mean_bgr = cv2.mean(image, mask=outer_half_mask)[:3]  # B, G, R
    mean_bgr = tuple(map(int, mean_bgr))

    # --- Convert to HSV for hue ---
    hsv_color = cv2.cvtColor(np.uint8([[mean_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
    piece_type_hue = int(hsv_color[0])

    # --- Find the closest hue from reference hues ---
    closest_type = 'p'
    closest_dist = float('inf')
    for hue, piece_type in hues:
        dist = hue_distance(piece_type_hue, hue)
        if dist < closest_dist:
            closest_dist = dist
            closest_type = piece_type

    # --- Use inner circle brightness to decide black/white piece ---
    mean_inner = cv2.mean(image, mask=mask_inner)
    mean_value_inner = mean_inner[2]  # Value (V) channel
    
    if mean_value_inner > 100:
        closest_type = closest_type.upper()  # white piece
    else:
        closest_type = closest_type.lower()  # black piece
    print(closest_type, mean_value_inner)
    return closest_type

def piece_coordinate(circle):
    x, y, r = (int(a) for a in circle)
    return (min(7, bisect(rows, y)), min(7, bisect(cols, x)))

def generate_fen(chess_grid):
    res = []
    seperator = ''
    for row in chess_grid:
        res.append(seperator)
        emptyCount = 0
        for square in row:
            if square == ' ':
                emptyCount += 1
            else:
                if emptyCount:
                    res.append(str(emptyCount))
                    emptyCount = 0
                res.append(square)
        if emptyCount:
            res.append(str(emptyCount))
        seperator = "/"
    res.append(" b KQkq - 0 1")
    return ''.join(res)

def print_board(board):
    print()
    print()
    for i, row in enumerate(board):
        print(8 - i, end=" ")
        for j, square in enumerate(row):
            if i % 2 == j % 2:
                print('\033[30;47m ', end='')
            else:
                print('\033[30;100m ', end='')
            if square in piece_icon:
                print(piece_icon[square], end=' ')
            else:
                #print(u'■' if i % 2 == j % 2 else u'□', end=' ')
                print('  ', end='')
            print('\033[0m', end='')
        print()
    print('  a b c d e f g h')
    print()
    print()

# TODO: Create the color ranges for each chess piece


while True:
    #try:
        #picam2.start_preview(Preview.DRM) here originally
        #picam2.start()
        #time.sleep(2)
        
        user_input = input("Press Enter to take source picture (\'q\' to quit): ")
        if user_input == 'q':
            picam2.close()
            break
        image = picam2.capture_image()
        image = picam2.capture_array()#[:, :, :3] - here originally
        
        bgr_image = image.copy()  # copy to draw on
        bgr_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGB2BGR)
        print(image) 
        
        #cv2.imshow('Original Image', image)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        #picam2.stop()
        #picam2.close() # <- here originally
        #print(image.shape) #img is taken in jpg/png format and we need BGR
       
        # break the loop if no image is taken
        if image is None:
            print("Error: Image not found or could not be loaded")
            break

        # convert the image to HSV
        #hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) -> this original line is not working
        
        #test code while original image was a jpeg
        #pil_image = Image.open(image)
        #rgb_image = np.array(pil_image)
        #bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR) 
        #print(bgr_image.shape)
        
        #testing new conversion

        
              # Convert to grayscale for Hough Circle detection
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        #cv2.imshow('Blurred image', gray)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        #picam2.stop()
        #picam2.close()
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, 1, 400,
            param1=20, param2=15, minRadius=90, maxRadius=110) #170, 180 og
        print("CIRCLES:", circles)

        chess_grid = np.full((8,8), ' ', dtype=str) #originally 8x8
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            circles = sorted(circles[0], key=lambda t: (t[0], t[1]))
            for idx, i in enumerate(circles):
                # Get the predicted piece (label)
                piece = get_piece(bgr_image, i)
                print(f"Circle {idx}: {piece} at ({i[0]}, {i[1]})")
                
                # Sample average BGR color in the outer ring
                x, y, r = map(int, i)
                mask_outer = np.zeros(bgr_image.shape[:2], dtype=np.uint8)
                cv2.circle(mask_outer, (x, y), r, 255, -1)
                mean_bgr = cv2.mean(bgr_image, mask=mask_outer)[:3]  # B, G, R
                mean_bgr = tuple(int(c) for c in mean_bgr)
                # Save piece to grid
                chess_grid[piece_coordinate(i)] = piece

                # Draw the circle
                cv2.circle(bgr_image, (i[0], i[1]), i[2], (0, 255, 255), 2)

                # Add text label (the piece or index)
                converted_bgr = cv2.cvtColor(bgr_image, cv2.COLOR_HSV2BGR)
                label = f"{piece}"  # could also use f"{idx}:{piece}"
                font_scale = 6
                thickness = 5
                text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                text_x = i[0] - text_size[0] // 2
                text_y = i[1] + text_size[1] // 2

                cv2.putText(
                    bgr_image, label, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness
                )
                
            print("1")
            cv2.imshow('Detected Circles', bgr_image)
            print("2")
            cv2.waitKey(0)
            print("3")
            cv2.destroyAllWindows()
            print("4")
        #cv2.imshow('Detected Circles', hsv)
        print("hi")
        print_board(chess_grid)
        #picam2.stop_preview()
        #picam2.close()
    #finally:
        #picam2.stop_preview()
        #icam2.stop()
        #picam2.close()
        #cv2.imshow('Detected Circles', hsv) # uncomment to see hsv image
        #print_board(chess_grid)
        #break
