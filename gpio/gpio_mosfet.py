import gpiozero
from time import sleep
import serial
from ina219 import INA219
import Adafruit_MCP4725
import Adafruit_ADS1x15
from math import log


FILAMENT_RELAY_PIN = 0
relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x41,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)


dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x60)

relay.on()

steps = list(range(2500, 3000))

with open("assets//filament_currents.csv", "w") as f:
    for step in steps:
        dac.set_voltage(step)
        sleep(0.1)

        current = ina.current()
        print(current, step)
        f.write(f"{current},{step}\n")

relay.off()
