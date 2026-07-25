from time import sleep
import gpiozero
import Photonic

XRAY = Photonic.Photonic(skip_initializations = True)

while True:
    XRAY.led(1, 0, 0)
    sleep(1)
    XRAY.led(0, 1, 0)
    sleep(1)
    XRAY.led(0, 0, 1)
    sleep(1)
