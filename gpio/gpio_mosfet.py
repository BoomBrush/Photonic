import gpiozero
from time import sleep
import serial
from ina219 import INA219
import Adafruit_MCP4725
import Adafruit_ADS1x15
from math import log


FILAMENT_RELAY_PIN = 0
FILAMENT_MOSFET_PIN = 24


def current(current):
    return int(104.96420406 * log(current) + 2029.7201648)


relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)


try:
    filament_dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x60)
except Exception:
    filament_dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x61)


#relay.on()

#desired_value = current(1800)
#print(desired_value)

#filament_dac.set_voltage(desired_value)

#while True:
#    print(round(ina.current(), 3))
#    sleep(0.1)


relay.on()

steps = list(range(2000, 2500, 10))

for step in steps:
    filament_dac.set_voltage(step)
    sleep(0.1)
    print(round(ina.current(), 3), step)

steps = list(range(2500, 2900, 1))

for step in steps:
    filament_dac.set_voltage(step)
    sleep(0.1)
    print(round(ina.current(), 3), step)

steps = list(range(2900, 4000, 10))

for step in steps:
    filament_dac.set_voltage(step)
    sleep(0.1)
    print(round(ina.current(), 3), step)



relay.off()
