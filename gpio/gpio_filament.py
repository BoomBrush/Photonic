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

I2C_BUS = 1


dac = Adafruit_MCP4725.MCP4725(busnum=I2C_BUS, address=0x60)
dac.set_voltage(0)

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x41,
             busnum=I2C_BUS)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)

adc = ADS1115()
relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)
relay.on()
dac.set_voltage(4095)

while True:
    #print("Relay on")
    #relay.on()
    #dac.set_voltage(4095)
    #sleep(0.25)
    #mosfet_voltage = (adc.average(3, 1) / 32768) * 4.096
    #print("MOSFET:", mosfet_voltage)
    #sleep(0.25)
    print("Current", ina.current())
    sleep(0.1)

    #print("Relay off")
    #relay.off()
    #dac.set_voltage(0)
    #sleep(0.5)
    #mosfet_voltage = (adc.average(3, 1) / 32768) * 4.096
    #print("MOSFET:", mosfet_voltage)
    #sleep(0.25)
    #print("Current", ina.current())
    #sleep(0.25)
