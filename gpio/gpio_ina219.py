from time import sleep

import sys
sys.path.insert(0, "/home/boombrush/Photonic")
from Photonic import PowerMonitor

filament = PowerMonitor(0x40)
voltage_3v3 = PowerMonitor(0x41)


print("Filament:")
print(f"{filament.voltage()}V, {filament.current()}mA, {filament.power()}mW")

print("Voltage 3.3v:")
print(f"{voltage_3v3.voltage()}V, {voltage_3v3.current()}mA, {voltage_3v3.power()}mW")


#print("HV Highside")
#print(f"{ina_hv_highside.voltage()}V, {ina_hv_highside.current()}mA, {ina_hv_highside.power()}mW")

#print("HV Lowside")
#print(f"{ina_hv_lowside.voltage()}V, {ina_hv_lowside.current()}mA, {ina_hv_lowside.power()}mW")

#print()




'''
ina_filament = INA219(shunt_ohms = 0.1,
                      max_expected_amps = 2.0,
                      address = 0x40,
                      busnum=2)

ina_filament.configure(voltage_range=ina_filament.RANGE_16V,
                      gain=ina_filament.GAIN_AUTO,
                      bus_adc=ina_filament.ADC_128SAMP,
                      shunt_adc=ina_filament.ADC_128SAMP)


ina_hv_highside= INA219(shunt_ohms = 0.1,
               max_expected_amps = 2.0,
               address = 0x41,
               busnum=2)

ina_hv_highside.configure(voltage_range=ina_hv_highside.RANGE_16V,
                 gain=ina_hv_highside.GAIN_AUTO,
                 bus_adc=ina_hv_highside.ADC_128SAMP,
                 shunt_adc=ina_hv_highside.ADC_128SAMP)



ina_hv_lowside= INA219(shunt_ohms = 0.1,
               max_expected_amps = 2.0,
               address = 0x44,
               busnum=2)

ina_hv_lowside.configure(voltage_range=ina_hv_lowside.RANGE_16V,
                 gain=ina_hv_lowside.GAIN_AUTO,
                 bus_adc=ina_hv_lowside.ADC_128SAMP,
                 shunt_adc=ina_hv_lowside.ADC_128SAMP)



'''
