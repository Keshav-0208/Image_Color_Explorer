import argparse
import cv2
import pandas as pd
import numpy as np

# Argument parsing
ap = argparse.ArgumentParser()
ap.add_argument('-i', '--image', required=True, help="Image Path")
args = vars(ap.parse_args())
img_path = args['image']
img = cv2.imread(img_path)

# Resize image to 1500 x 900 if not already at that size
desired_width, desired_height = 1500, 900
current_height, current_width = img.shape[:2]

if current_width != desired_width or current_height != desired_height:
    img = cv2.resize(img, (desired_width, desired_height))

# Global variables
clicked = False
r = g = b = xpos = ypos = 0
zoom_scale = 1.0
zoom_factor = 1.1
shift_x = 0
shift_y = 0

# Load color data
index = ['color', 'colorname', 'hex', 'R', 'G', 'B']
file = pd.read_csv("colors.csv", names=index, header=None)

def getcolorname(R, G, B):
    minimum = 10000
    colorname = ""
    for i in range(len(file)):
        d = abs(R - int(file.loc[i, "R"])) + abs(G - int(file.loc[i, "G"])) + abs(B - int(file.loc[i, "B"]))
        if d < minimum:
            minimum = d
            colorname = file.loc[i, "colorname"]
    return colorname

def drawfunction(event, x, y, flags, param):
    global b, g, r, xpos, ypos, clicked, zoom_scale, zoom_factor, img, shift_x, shift_y

    if event == cv2.EVENT_LBUTTONDBLCLK:
        clicked = True
        xpos = int((x - shift_x) / zoom_scale)
        ypos = int((y - shift_y) / zoom_scale)
        b, g, r = img[ypos, xpos]
        b = int(b)
        g = int(g)
        r = int(r)
    elif event == cv2.EVENT_MOUSEWHEEL:
        old_zoom_scale = zoom_scale
        if flags > 0:  # Scroll up
            zoom_scale *= zoom_factor
        else:  # Scroll down
            zoom_scale /= zoom_factor
        zoom_scale = max(1.0, zoom_scale)  # Prevent zooming out too much

        # Adjust the shift to keep the cursor point in the same position
        shift_x = x - (x - shift_x) * (zoom_scale / old_zoom_scale)
        shift_y = y - (y - shift_y) * (zoom_scale / old_zoom_scale)

        # Clamp the shift values to keep the image within the window
        shift_x = min(0, max(shift_x, -img.shape[1] * zoom_scale + img.shape[1]))
        shift_y = min(0, max(shift_y, -img.shape[0] * zoom_scale + img.shape[0]))

cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback('image', drawfunction)

while True:
    resized_img = cv2.resize(img, None, fx=zoom_scale, fy=zoom_scale, interpolation=cv2.INTER_LINEAR)

    # Clamp the translation to the image boundaries
    shift_x = min(0, max(shift_x, -resized_img.shape[1] + img.shape[1]))
    shift_y = min(0, max(shift_y, -resized_img.shape[0] + img.shape[0]))

    translated_img = cv2.warpAffine(resized_img, np.float32([[1, 0, shift_x], [0, 1, shift_y]]), (resized_img.shape[1], resized_img.shape[0]))

    if clicked:
        rect_x_start = int(xpos * zoom_scale + shift_x)
        rect_x_end = rect_x_start + 750
        rect_y_start = int(ypos * zoom_scale + shift_y)
        rect_y_end = rect_y_start + 60

        text_x = rect_x_start + 20
        text_y = rect_y_start + 40

        # Check if the rectangle goes out of the right edge
        if rect_x_end > translated_img.shape[1]:
            rect_x_start = translated_img.shape[1] - 750
            text_x = rect_x_start + 20
        
        # Check if the rectangle goes out of the bottom edge
        if rect_y_end > translated_img.shape[0]:
            rect_y_start = translated_img.shape[0] - 60
            text_y = rect_y_start + 40

        # Draw the rectangle and text
        cv2.rectangle(translated_img, (rect_x_start, rect_y_start), 
                      (rect_x_start + 750, rect_y_start + 60), (b, g, r), -1)
        text = getcolorname(r, g, b) + ' R=' + str(r) + ' G=' + str(g) + ' B=' + str(b)
        cv2.putText(translated_img, text, (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        if r + g + b >= 600:
            cv2.putText(translated_img, text, (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.imshow("image", translated_img)

    key = cv2.waitKey(20) & 0xFF
    if key == 27:  # Escape key to exit
        break
    elif key == ord('r'):  # 'r' key to reset zoom
        zoom_scale = 1.0
        shift_x = 0
        shift_y = 0

cv2.destroyAllWindows()
