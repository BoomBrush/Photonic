import Photonic
from time import sleep

XRAY = Photonic.Machine(ignore_camera=True)


while True:
    print("Shutter on")
    XRAY.camera_shutter(True)
    sleep(2)

    print("Shutter off")
    XRAY.camera_shutter(False)
    sleep(2)


