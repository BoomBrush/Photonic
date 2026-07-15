from time import sleep
import Photonic

XRAY = Photonic.Machine()

img = XRAY.capture(30, 2000) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    img.save(f"imgs/test image.jpg")
else:
    print("Image failed")

XRAY.finished()
