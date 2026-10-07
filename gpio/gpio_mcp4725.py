import Adafruit_MCP4725
import time
import gpiozero
from ina219 import INA219

FILAMENT_RELAY_PIN = 0
FILAMENT_MOSFET_PIN = 24

filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)
filament_mosfet = gpiozero.PWMOutputDevice(FILAMENT_MOSFET_PIN)

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.0,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)


dac=Adafruit_MCP4725.MCP4725(busnum=1, address=0x60)

filament_relay.on()

try:
    while True:
        for x in range(2000,4096,1):
            dac.set_voltage(x)
            current = ina.current()
            print(x, current)
            time.sleep(0.1)
        break
except Exception:
    print("issue")
    pass
