'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''
#import Photonic
#import RPi.GPIO as GPIO
#from gpiozero import LED, PWMLED, Button
import gpiozero
from time import sleep

hv_pwm_pin = 19			# PWM pin connected to LED
hv_active_pin = 27
hv_power_pin = 5

hv_pwm = gpiozero.PWMOutputDevice(hv_pwm_pin)
hv_active = gpiozero.OutputDevice(hv_active_pin)
hv_present = gpiozero.InputDevice(hv_power_pin)


if hv_present.value == 1:
    print("HV PSU Detected")
else:
    print("WARNING: HV PSU NOT DETECTED")

hv_pwm.value = 0.4
print(f"Pin {hv_pwm_pin} set to {hv_pwm.value}")

hv_active.on()
print(f"Pin {hv_active_pin} HIGH")

sleep(0.3)

print(f"Pin {hv_active_pin} LOW")
hv_active.off()

print(f"Pin {hv_pwm_pin} set to 0")
hv_pwm.value = 0
