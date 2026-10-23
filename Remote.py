from time import sleep
from PIL import ImageDraw, ImageFont
import Photonic, sys
import numpy, cv2

XRAY = Photonic.Photonic(capture_method=Photonic.DIRECT_CAPTURE)

power = int(sys.argv[1])
duration = int(sys.argv[2])

if len(sys.argv) == 4:
    filename = sys.argv[3]
else:
    filename = "remote"

if XRAY.system_check():
    scan = XRAY.capture(power, duration)

    if scan.img:
        scan.img.save(f"imgs/{filename}.jpg")
    else:
        print("Image failed to be captured")
else:
    print("System check failed")

XRAY.finish()
