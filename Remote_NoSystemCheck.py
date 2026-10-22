from time import sleep
from PIL import ImageDraw, ImageFont
import Photonic, sys
import numpy, cv2

XRAY = Photonic.Photonic(ignore_exceptions=True, disable_led=True)

power = int(sys.argv[1])
duration = int(sys.argv[2])

if len(sys.argv) == 4:
    filename = sys.argv[3]
else:
    filename = "remote"

scan = XRAY.capture(power, duration) # Power (%), Time (ms)

filename = f"{filename}"

if scan.img:
    scan.img.save(f"imgs/{filename}.jpg")
else:
    print("Image failed to be captured")

XRAY.finish()
