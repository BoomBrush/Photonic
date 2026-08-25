from time import sleep
from PIL import ImageDraw
import numpy, cv2
import Photonic
import SystemCheck

XRAY = Photonic.Photonic()

if SystemCheck.system_check(XRAY):
    print("System check passed. Proceeding...")

    img = XRAY.capture(100, 1000) # Power (%), Time (ms), FilamentCurrent (Amps)

    if img:
        img.save("imgs/SingleScan.jpg")
        print("Image saved")
    else:
        print("Image failed")
else:
    print("System check failed")

XRAY.finished()
