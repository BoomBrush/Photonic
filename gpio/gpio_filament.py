import gpiozero, sys, os
from time import sleep
import serial
from ina219 import INA219
import Adafruit_MCP4725
from math import log
import Adafruit_ADS1x15

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from Photonic import ADS1115

ADC_SAMPLES = 10
FILAMENT_RELAY_PIN = 0

try:
    filament_dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x60)
    filament_dac.set_voltage(0)
    print("0x60")
except OSError:
    filament_dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x61)
    filament_dac.set_voltage(0)
    print("0x61")

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)

adc = ADS1115()
filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)



while True:
    filament_relay.on()
    filament_dac.set_voltage(4095)
    mosfet_voltage = (adc.average(3, 1) / 32768) * 4.096
    print("ON")
    sleep(0.5)
    print(f"Current: {ina.current()} MOSFET: {mosfet_voltage}")
    sleep(1)

    filament_relay.off()
    filament_dac.set_voltage(0)
    mosfet_voltage = (adc.average(3, 1) / 32768) * 4.096
    print("OFF")
    sleep(0.5)
    print(f"Current: {ina.current()} MOSFET: {mosfet_voltage}")
    sleep(1)
