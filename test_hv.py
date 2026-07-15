from time import sleep
import Photonic

XRAY = Photonic.Machine(ignore_camera=True)

# Wait for PSU to sync with PWM
sleep(1)

while True:
    # Turn HV on
    print("HV ON")
    XRAY.hv_pwm(50)
    XRAY.hv(True)
    sleep(2)

    # Turn HV off
    print("HV OFF")
    XRAY.hv(False)
    XRAY.hv_pwm(0)
    sleep(2)

XRAY.kill()
