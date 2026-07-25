from ina219 import INA219
from time import sleep

ina_filament = INA219(shunt_ohms = 0.1,
                      max_expected_amps = 2.0,
                      address = 0x40,
                      busnum=1)

ina_filament.configure(voltage_range=ina_filament.RANGE_16V,
                      gain=ina_filament.GAIN_AUTO,
                      bus_adc=ina_filament.ADC_128SAMP,
                      shunt_adc=ina_filament.ADC_128SAMP)


ina_hv= INA219(shunt_ohms = 0.1,
               max_expected_amps = 2.0,
               address = 0x41,
               busnum=1)

ina_hv.configure(voltage_range=ina_hv.RANGE_16V,
                 gain=ina_hv.GAIN_AUTO,
                 bus_adc=ina_hv.ADC_128SAMP,
                 shunt_adc=ina_hv.ADC_128SAMP)



#while True:
print("Filament:")
print(f"{ina_filament.voltage()}V, {ina_filament.current()}A, {ina_filament.power()}mW")

print("HV")
print(f"{ina_hv.voltage()}V, {ina_hv.current()}A, {ina_hv.power()}mW")

print()
#    sleep(1)
