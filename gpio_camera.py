import Photonic
from time import sleep

XRAY = Photonic.Machine(ignore_camera=True)

while True:
    print("Camera off")
    XRAY.gpio_camera_power.off()

    sleep(1)

    print("Camera on")
    XRAY.gpio_camera_power.on()
    sleep(1)


