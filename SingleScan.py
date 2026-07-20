from time import sleep
import Photonic

XRAY = Photonic.Machine()

img = XRAY.capture(40, 2000, 0.00) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    img.save(f"imgs/test image 40 2000 0.00Amps.jpg")
    print("Image saved")
else:
    print("Image failed")

XRAY.finished()
