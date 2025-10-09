import csv
import math
import numpy as np
import time
from bisect import bisect
import os

from picamera2 import Picamera2, Preview

#os.environ["QT_DEBUG_PLUGINS"] = "1"
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/home/raspberrypi/Documents/robot_arm/venv/lib/python3.11/site-packages/cv2/qt/plugins/platforms"

import cv2  # Only after setting the environment variable

picam2 = Picamera2()

#picam2.preview_size = (3280, 2464)

camera_config = picam2.create_preview_configuration()#main={"size": (1640, 1232)})
picam2.configure(camera_config)

# Setting chessboard grid dimension
grid_dimension = (8,2)

# Experiment with thresholds once we have real pictures
# Saturation of lower bound might need to be increased
color_threshold_lower = (0, 100, 0)
color_threshold_upper= (255, 255, 255)

black = (0, 0, 0)
white = (255, 255, 255)
blue = (82, 113, 255)
green = (0, 191, 99)
red = (255, 49, 49)
pink = (255, 102, 196)
orange = (255, 145, 77)
yellow = (255, 222, 89)

rows = [1232 // 8 * i for i in range(8)]
cols = [1640 // 8 * i for i in range(8)]

def get_hue(rgb_color):
    rgb_array = np.uint8([[list(rgb_color)]])
    hsv_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
    hsv_color = tuple(hsv_array[0][0])
    return hsv_color[0]

hues = (
    (get_hue(blue), 'p'),
    (get_hue(green), 'b'),
    (get_hue(red), 'k'),
    (get_hue(pink), 'n'),
    (get_hue(orange), 'q'),
    (get_hue(yellow), 'r')
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

def get_piece(image, circle):
    x, y, r = (int(a) for a in circle)
    if y < image.shape[0] // 2:
        piece_type_color = image[y+r-2][x]
    else:
        piece_type_color = image[y-r+2][x]
    #print(y+r-3, x)
    #print(piece_type_color)
    piece_type_hue = piece_type_color[0]
    closest_type = 'p'
    closest_dist = float('inf')
    for hue, piece_type in hues:
        dist = piece_type_hue - hue
        if dist < closest_dist:
            closest_dist = dist
            closest_type = piece_type
    piece_center_color = image[y][x]
    piece_center_val = piece_center_color[2]
    if piece_center_val > 128:
        closest_type = closest_type.upper()
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
    picam2.start_preview(Preview.DRM)
    picam2.start()
    time.sleep(2)
    user_input = input("Press Enter to take source picture (\'q\' to quit): ")
    if user_input == 'q':
        picam2.close()
        break
    image = picam2.capture_array()#[:, :, :3]
    cv2.imshow('Original Image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    picam2.close()
    print(image)
    # break the loop if no image is taken
    if image is None:
        print("Error: Image not found or could not be loaded")
        break

    # convert the image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # isolate the pixels based on the lower and upper bounds
    mask_sat = cv2.inRange(hsv, color_threshold_lower, color_threshold_upper)
    # Colored pixels = True, Gray pixels = False
    imask_sat = mask_sat > 0
    # Create new image setting everything that is not green white
    colors = np.full(image.shape[:2], 255, dtype=np.uint8)
    # Setting every color to black
    colors[imask_sat] = 0

    # blur the images, used for live image capture
    blurred = cv2.GaussianBlur(colors, (9,9), 2)
    
    # display images
    # cv2.imshow('image.jpg', image)
    # cv2.imshow('green.jpg', green)
    # cv2.imshow('blurred.jpg', blurred)

    '''
    # detect grid pattern
    ret, corners = cv2.findCirclesGrid(
        green, 
        grid_dimension,
        flags=cv2.CALIB_CB_SYMMETRIC_GRID + cv2.CALIB_CB_CLUSTERING
    )
    
    print(ret, corners)
    '''
    
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, 1, 20, param1=20, param2=10, minRadius=20, maxRadius=30)
    
    #print(circles)

    chess_grid = np.full((8,8), ' ', dtype=str)
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        circles = sorted(circles[0], key=lambda t: (t[0], t[1]))
        for i in circles:
            piece = get_piece(hsv, i)
            chess_grid[piece_coordinate(i)] = piece
            cv2.circle(hsv, (i[0], i[1]), i[2], (0, 255, 255), 2)
        
        cv2.imshow('Detected Circles', hsv)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    print_board(chess_grid)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
