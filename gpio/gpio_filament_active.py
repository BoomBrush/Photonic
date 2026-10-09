import Adafruit_MCP4725
import gpiozero
from time import sleep
import serial
from ina219 import INA219
from math import log


class Interpolation():
    def __init__(self, filename):
        with open(filename,'rb') as file:
            self.lines = file.readlines()
            self.dacs = []
            self.currents = []

        for line in self.lines:
            row = line.decode().split(" ")

            current_value = float(row[0])
            dac_value = float(row[1][:-1])

            self.dacs.append(dac_value)
            self.currents.append(current_value)

    def dac_to_current(self, value):
        for i in list(range(len(self.dacs))):
            dac = self.dacs[i]

            if dac > value:
                return (self.currents[i] + self.currents[i-1]) / 2

    def current_to_dac(self, value):
        for i in list(range(len(self.currents))):
            current = self.currents[i]

            if self.currents[i] > value:
                return int((self.dacs[i] + self.dacs[i-1]) / 2)


FILAMENT_RELAY_PIN = 0
relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 3.1,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)



dac = Adafruit_MCP4725.MCP4725(busnum=1, address=0x60)

interpolation = Interpolation("assets//filament_currents.csv")

relay.on()

target_current = 1500
target = interpolation.current_to_dac(target_current)
dac.set_voltage(target)
mosfet_value = 2000

while True:
    mosfet_current = ina.current()

    if mosfet_current < target_current:
        difference = target_current - mosfet_current
        mosfet_value += 20

        print(f"LESS THAN - mosfet_current: {mosfet_current}, difference: {difference}")
    elif mosfet_current > target_current:
        difference = mosfet_current - target_current
        mosfet_value -= 20

        print(f"GREATER THAN - mosfet_current: {mosfet_current}, difference: {difference}")

    dac.set_voltage(mosfet_value)
    sleep(0.05)

