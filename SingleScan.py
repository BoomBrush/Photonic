from time import sleep
import Photonic

XRAY = Photonic.Machine()

img = XRAY.capture(60, 3000) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    img.save(f"imgs/test image.jpg")
    print("Image saved")
else:
    print("Image failed")

XRAY.finished()
