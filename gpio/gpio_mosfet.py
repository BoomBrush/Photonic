import gpiozero
from time import sleep
import serial
from ina219 import INA219
import Adafruit_MCP4725
import Adafruit_ADS1x15

FILAMENT_RELAY_PIN = 0
FILAMENT_MOSFET_PIN = 24

ADC_SAMPLES = 10

class ADS1115():
    def __init__(self):
        self.ads1115 = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)

    def average(self, channel, gain):
        sum = 0

        for _ in range(ADC_SAMPLES):
            sum += self.ads1115.read_adc(channel, gain=gain)

        return sum / ADC_SAMPLES


filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)


adc = ADS1115()

try:
    filament_dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x60)
except Exception:
    filament_dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x61)


filament_relay.on()

for step in list(range(1800, 4095)):
    filament_dac.set_voltage(step)
    sleep(0.05)
    mosfet_voltage = (adc.ads1115.read_adc(3, 1) / 32768) * 4.096
    current = ina.current()
    print(round(current, 3), step)

filament_relay.off()
