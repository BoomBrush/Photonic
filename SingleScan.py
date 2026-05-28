from time import sleep
import Photonic

XRAY = Photonic.Machine()

img = XRAY.capture(40, 4000) # 40% for 4 seconds

if img:
    img.save(f"imgs/test image.jpg")
else:
    print("Image failed")

XRAY.stop()
