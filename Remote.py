from time import sleep
from PIL import ImageDraw, ImageFont
import Photonic, sys
import numpy, cv2
from SystemCheck import system_check

XRAY = Photonic.Photonic(raise_exceptions=False)

sleep(10)

system_check(XRAY)

power = int(sys.argv[1])
duration = int(sys.argv[2])

if len(sys.argv) == 4:
    filename = sys.argv[3]
else:
    filename = "remote"

img = XRAY.capture(power, duration) # Power (%), Time (ms)

if img:
    img.convert('L').save(f"imgs/{filename}.jpg")
    print("Done")
else:
    print("Image failed to be captured")

XRAY.finished()
