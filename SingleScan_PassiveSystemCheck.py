from time import sleep
from PIL import ImageDraw
import numpy, cv2
import Photonic
import SystemCheck

XRAY = Photonic.Photonic(raise_exceptions=False)

SystemCheck.system_check(XRAY)

img = XRAY.capture(100, 10000) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    img.save("imgs/SingleScan_OLD_TUBE_100_10000.jpg")
    print("Image saved")
else:
    print("Image failed")

XRAY.finished()
