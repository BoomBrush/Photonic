
from time import sleep
from PIL import ImageDraw, ImageFont
import Photonic, sys
import numpy, cv2

XRAY = Photonic.Photonic()

power = int(sys.argv[1])
duration = int(sys.argv[2])

if len(sys.argv) == 4:
    filename = sys.argv[3]
else:
    filename = "remote"

if XRAY.system_check():
    scan = XRAY.capture(power, duration)

    print("Duration:", scan.actual_duration)

    if scan:
        scan.save(f"imgs/{filename}.jpg")
    else:
        print("Image failed to be captured")
else:
    print("System check failed")

XRAY.finish()
