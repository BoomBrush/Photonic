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

if scan:
    scan.save(f"imgs/{filename}.jpg")
    print("Duration:", scan.actual_duration)
else:
    print("Image failed to be captured")

XRAY.finish()
