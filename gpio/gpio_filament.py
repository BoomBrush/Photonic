import gpiozero
from time import sleep
import serial
from ina219 import INA219

#import sys
#sys.path.append("..")
#from Photonic import *

FILAMENT_RELAY_PIN = 24

filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)


ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)

# INA219 Init


while True:
    print("Filament ON")
    filament_relay.on()
    sleep(1)
    print(f"{ina.voltage()}V {int(ina.current())}mA")
    sleep(2)

    print("Filament OFF")
    filament_relay.off()
    sleep(1)
    print(f"{ina.voltage()}V {int(ina.current())}mA")
    sleep(2)
