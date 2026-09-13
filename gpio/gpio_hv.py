'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''
#import Photonic
#import RPi.GPIO as GPIO
#from gpiozero import LED, PWMLED, Button
import gpiozero
from time import sleep
from ina219 import INA219

hv_pwm_pin = 13			# PWM pin connected to LED
hv_active_pin = 0
hv_power_pin = 9

#hv_pwm = gpiozero.PWMOutputDevice(hv_pwm_pin)
hv_pwm = gpiozero.OutputDevice(hv_pwm_pin)
hv_active = gpiozero.OutputDevice(hv_active_pin)
hv_present = gpiozero.InputDevice(hv_power_pin)

HV_R1_RESISTANCE = 70_750_000
HV_R2_RESISTANCE = 21_800


#def calculate_hv(vout):
#    return vout / (HV_R2_RESISTANCE / (HV_R2_RESISTANCE + HV_R1_RESISTANCE))


#ina = INA219(shunt_ohms = 0.1,
#             max_expected_amps = 2.0,
#             address = 0x41,
#             busnum=2)

#ina.configure(voltage_range=ina.RANGE_16V,
#              gain=ina.GAIN_AUTO,
#              bus_adc=ina.ADC_128SAMP,
#              shunt_adc=ina.ADC_128SAMP)

if hv_present.value == 1:
    print("HV PSU Detected")
else:
    print("WARNING: HV PSU NOT DETECTED")

while True:
    hv_pwm.value = 0.35
    print(f"Pin {hv_pwm_pin} set to {hv_pwm.value}")
    hv_active.on()
    print(f"Pin {hv_active_pin} HIGH")
    sleep(3)

    print(f"Pin {hv_active_pin} LOW")
    hv_active.off()
    print(f"Pin {hv_pwm_pin} set to 0")
    hv_pwm.value = 0
    sleep(3)
