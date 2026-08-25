from time import sleep
import Photonic
import numpy, cv2

XRAY = Photonic.Photonic()

img = XRAY.capture(50, 1000) # Power (%), Time (ms), FilamentCurrent (Amps)
print(img, type(img))

if img:
    img.save("imgs/SingleScan.jpg")

    print("Image saved")
else:
    print("Image failed")

XRAY.finished()
