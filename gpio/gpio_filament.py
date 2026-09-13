import gpiozero
from time import sleep
import serial
from ina219 import INA219

#import sys
#sys.path.append("..")
#from Photonic import *

FILAMENT_RELAY_PIN = 16

filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)


#ina = INA219(shunt_ohms = 0.1,
#             max_expected_amps = 3.0,
#             address = 0x40,
#             busnum=1)

#ina.configure(voltage_range=ina.RANGE_16V,
#              gain=ina.GAIN_AUTO,
#              bus_adc=ina.ADC_128SAMP,
#              shunt_adc=ina.ADC_128SAMP)

# INA219 Init

def filament_on():
    filament_relay.on()

def filament_off():
    filament_relay.off()


while True:
    print("Filament ON")
    filament_on()
#    sleep(0.5)
#    print(f"{ina.voltage()}V {round(ina.current()/1000, 3)}A")
    sleep(2)

    print("Filament OFF")
    filament_off()
#    sleep(0.5)
#    print(f"{ina.voltage()}V {round(ina.current()/1000, 3)}A")
    sleep(2)
