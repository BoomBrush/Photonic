import sys
sys.path.append("/home/boombrush/Photonic")
import Photonic
from time import sleep

XRAY = Photonic.Photonic(raise_exceptions=False)


while True:
    print("Shutter on")
    XRAY.camera_shutter(True)
    sleep(2)

    print("Shutter off")
    XRAY.camera_shutter(False)
    sleep(2)


