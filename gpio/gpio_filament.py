'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''

import gpiozero
from time import sleep
import serial
from ina219 import INA219
#from Photonic import PowerMonitor

filament_mosfet_pin = 18			# PWM pin connected to LED
filament_relay_pin = 23

filament_mosfet = gpiozero.PWMOutputDevice(filament_mosfet_pin)
filament_relay = gpiozero.OutputDevice(filament_relay_pin)


ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 2.0,
             address = 0x40,
             busnum=2)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)

# INA219 Init

def filament_on():
    filament_mosfet.value = 1.0
    filament_relay.on()

def filament_off():
    filament_mosfet.value = 0.0
    filament_relay.off()


while True:
    print("Filament ON")
    filament_on()
    sleep(0.5)
    print(f"{ina.voltage()}V {ina.current()}")
    sleep(3)

    print("Filament OFF")
    filament_off()
    sleep(0.5)
    print(f"{ina.voltage()}V {ina.current()}")
    sleep(1)
