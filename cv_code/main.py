import cv2
import numpy as np
import math
from bisect import bisect

import chess
import chess.engine
import time

import os # only for demo

stockfish_path = "./stockfish/src/stockfish"
engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

# Setting chessboard grid dimension
grid_dimension = (8,2)
# Setting HSV lower and upper bound ranges
lower_green = (25, 50, 90)
higher_green = (80, 255, 255)

# Experiment with thresholds once we have real pictures
# Saturation of lower bound might need to be increased
color_threshold_lower = (0, 10, 0)
color_threshold_upper= (255, 255, 255)

black = (0, 0, 0)
white = (255, 255, 255)
blue = (82, 113, 255)
green = (0, 191, 99)
red = (255, 49, 49)
pink = (255, 102, 196)
orange = (255, 145, 77)
yellow = (255, 222, 89)

rows = [60, 120, 180, 240, 300, 360, 420, 480]
cols = [140, 200, 260, 320, 380, 440, 500, 560]

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
    piece_type_color = image[y+r-2][x]
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
    return (bisect(rows, y), bisect(cols, x))

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

demo_moves = [
    "e2e4",
    "e7e5",
    "g1f3",
    "d7d6",
    "d2d4",
    "c8g4",
    "d4e5",
    "g4f3",
    "d1f3",
    "d6e5",
    "f1c4",
    "g8f6",
    "f3b3",
    "d8e7",
    "b1c3",
    "c7c6",
    "c1g5",
    "b7b5",
    "c3b5",
    "c6b5",
    "c4b5",
    "b8d7",
    "e1c1",
    "a8d8",
    "d1d7",
    "d8d7",
    "h1d1",
    "e7e6",
    "b5d7",
    "f6d7",
    "b3b8",
    "d7b8",
    "d1d8"
]

images = sorted(os.listdir("./images/chess_game_sequence/eight_colors"))
for move, image in zip(demo_moves + ["Checkmate!"], [images[33]] + images[15:33] + images[:15]):
    # load the image
    image = cv2.imread(f"./images/chess_game_sequence/eight_colors/{image}")
    # break the loop if no image is found or loaded
    if image is None:
        print("Error: Image not found or could not be loaded")
        break

    # convert the image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # isolate the pixels based on the lower and upper bounds
    mask_green = cv2.inRange(hsv, color_threshold_lower, color_threshold_upper)
    # Green pixels = True, Not green = False
    imask_green = mask_green>0
    # Create new image setting everything that is not green white
    green = np.full(image.shape, (255, 255, 255), dtype=np.uint8)
    # Setting everything green to black
    green[imask_green] = (0,0,0)

    # blur the images, used for live image capture
    blurred = cv2.GaussianBlur(green, (9,9), 2)

    cv2.imshow('Detected Circles', green)
    
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
    gray = cv2.cvtColor(green, cv2.COLOR_BGR2GRAY)
    
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, param1=20, param2=10, minRadius=15, maxRadius=30)
    
    #print(circles)

    chess_grid = np.full((8,8), ' ', dtype=str)
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        circles = sorted(circles[0], key=lambda t: (t[0], t[1]))
        for i in circles:
            piece = get_piece(hsv, i)
            chess_grid[piece_coordinate(i)] = piece
            cv2.circle(green, (i[0], i[1]), i[2], (0, 255, 0), 2)
        for r in rows:
            cv2.line(green, (80, r), (500, r), (0, 0, 255), 5)
        for c in cols:
            cv2.line(green, (c, 0), (c, 400), (0, 0, 255), 5)
        
        # cv2.imshow('Detected Circles', green)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    print_board(chess_grid)
    print(f"Engine's move: {move}")

    cv2.namedWindow('Detected Circles:', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Detected Circles:', 640, 480)
    cv2.moveWindow('Detected Circles:', 1000, 1200)
    cv2.imshow('Detected Circles:', green)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

cv2.destroyAllWindows()
