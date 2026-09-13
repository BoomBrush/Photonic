from time import sleep
import gpiozero, sys
sys.path.append("/home/boombrush/Photonic")
import Photonic

XRAY = Photonic.Photonic(raise_exceptions=False)

while True:
    XRAY.led(1, 0, 0)
    sleep(1)
    XRAY.led(0, 1, 0)
    sleep(1)
    XRAY.led(0, 0, 1)
    sleep(1)
