from time import sleep
from PIL import ImageDraw, ImageFont
import Photonic, sys
import numpy, cv2
import SystemCheck

XRAY = Photonic.Photonic()

sleep(10)

if SystemCheck.system_check(XRAY):

    power = int(sys.argv[1])
    duration = int(sys.argv[2])

    if len(sys.argv) == 4:
        filename = sys.argv[3]
    else:
        filename = "remote"

    img = XRAY.capture(power, duration) # Power (%), Time (ms)

    if img:
        img.save(f"imgs/{filename}.jpg")
        print("Done")
    else:
        print("Image failed to be captured")
else:
    print("System check failed")

XRAY.finished()
