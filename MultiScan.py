from time import sleep
import Photonic
import SystemCheck

POWER = 80
DURATION = 2000
NUMBER_OF_SCANS = 5

XRAY = Photonic.Photonic(ignore_ina219=True)

SystemCheck.system_check(XRAY)

for i in range(NUMBER_OF_SCANS):
    print("Scan", i + 1)
    img = XRAY.capture(POWER, DURATION)
    img.save("imgs/" + str(i) + ".jpg")

XRAY.finished()
