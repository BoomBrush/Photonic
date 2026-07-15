from time import sleep
import Photonic

XRAY = Photonic.Machine(ignore_camera=True, ignore_arduino=True)

# Wait for PSU to sync with PWM
print("PWM On 0.2")
XRAY.hv_pwm(0.2)

# Turn filament on
print("Filament ON")
XRAY.filament(True)

sleep(1)

# Turn HV on
print("HV ON")
XRAY.hv_enable(True)

sleep(5)

# Turn HV and filament off
print("HV OFF")
XRAY.hv_enable(False)
XRAY.hv_pwm(0)
XRAY.filament(False)

XRAY.kill()
