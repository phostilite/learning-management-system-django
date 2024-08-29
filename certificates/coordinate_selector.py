# Import the required libraries
import cv2
import os
from django.conf import settings

# Define a function to display the coordinates of
# the points clicked on the image
def click_event(event, x, y, flags, params):
   if event == cv2.EVENT_LBUTTONDOWN:
      print(f'Coordinates: ({x}, {y})')

      # Put coordinates as text on the image
      cv2.putText(img, f'({x}, {y})', (x, y),
                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

      # Draw a point on the image
      cv2.circle(img, (x, y), 3, (0, 255, 255), -1)


# Construct the full path to the image file
image_path = os.path.join(settings.BASE_DIR, 'certificate.png')

# Read the input image (your certificate template)
img = cv2.imread(image_path)

# Create a window
cv2.namedWindow('Select Coordinates')

# Bind the callback function to the window
cv2.setMouseCallback('Select Coordinates', click_event)

# Display the image
while True:
   cv2.imshow('Select Coordinates', img)
   k = cv2.waitKey(1) & 0xFF
   if k == 27:  # Press 'Esc' to exit
      break

# Close all OpenCV windows
cv2.destroyAllWindows()