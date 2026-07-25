from time import sleep
import Photonic
import numpy, cv2

XRAY = Photonic.Photonic()

img = XRAY.capture(100, 3000, 1.8) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    image = numpy.array(img)
    greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("imgs/test image.jpg", greyscale)

    print("Image saved")
else:
    print("Image failed")

XRAY.finished()
