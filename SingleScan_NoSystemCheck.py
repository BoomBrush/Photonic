from time import sleep
import Photonic

XRAY = Photonic.Photonic(raise_exceptions=False)

sleep(5)
img = XRAY.capture(100, 2000) # Power (%), Time (ms), Filament power (%)

if img:
    img.save("imgs/SingleScan.jpg")

    print("Image saved")
else:
    print("Image failed")

XRAY.finished()
