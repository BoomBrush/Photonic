import sys
sys.path.append("/home/boombrush/Photonic")
import Photonic
from time import sleep

XRAY = Photonic.Photonic()


while True:
    print("Shutter on")
    XRAY.dslr.trigger(True)
    sleep(2)

    print("Shutter off")
    XRAY.dslr.trigger(False)
    sleep(8)


