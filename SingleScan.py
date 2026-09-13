from time import sleep
import Photonic
from SystemCheck import system_check

XRAY = Photonic.Photonic(raise_exceptions=False)

if system_check(XRAY):
    print("System check passed. Proceeding...")
    img = XRAY.capture(75, 2000) # HV Power (%), Time (ms)

    if img:
        img.save("imgs/SingleScan.jpg")
        print("Image saved")
    else:
        print("Image failed")
else:
    print("System check failed")

XRAY.finished()
