import sys
sys.path.append("/home/boombrush/Photonic")
import Photonic
from time import sleep

XRAY = Photonic.Photonic(ignore_exceptions=True)


while True:
    print("Shutter on")
    XRAY.dslr.trigger(True)
    sleep(1)

    print("Shutter off")
    XRAY.dslr.trigger(False)
    sleep(1)


