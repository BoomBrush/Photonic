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


def current_to_value(value):
    return int(104.96420406 * log(value) + 2029.7201648)

def value_to_current(value):
    return 4.06553538 * 10**-9 * 1.00956566**value


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
relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)

relay.on()

filament_dac.set_voltage(4095)

while True:
    print(f"Current: {round(ina.current(), 0)}")
    sleep(0.1)
#
#    filament_relay.off()
#    filament_dac.set_voltage(0)
#    print("OFF")
#    mosfet_voltage = (adc.average(3, 1) / 32768) * 4.096
#    sleep(0.5)
#    print(f"Current: {ina.current()} MOSFET: {mosfet_voltage}")
#    sleep(1)
