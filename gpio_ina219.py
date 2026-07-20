from ina219 import INA219
from time import sleep

ina = INA219(shunt_ohms = 0.1,
             max_expected_amps = 2.0,
             address = 0x40,
             busnum=1)

ina.configure(voltage_range=ina.RANGE_16V,
              gain=ina.GAIN_AUTO,
              bus_adc=ina.ADC_128SAMP,
              shunt_adc=ina.ADC_128SAMP)

print(ina.RANGE_16V, ina.GAIN_AUTO, ina.ADC_128SAMP, ina.ADC_128SAMP)

while True:
    v = ina.voltage()
    i = ina.current()
    p = ina.power()

    print("Voltage:", v)
    print("Current:", i)
    print("Power:", p)

    sleep(1)
