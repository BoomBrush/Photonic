'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''

import gpiozero
from time import sleep
import serial

filament_pin = 18				# PWM pin connected to LED
filament_relay_pin = 24

filament = gpiozero.PWMOutputDevice(filament_pin)
filament_relay = gpiozero.OutputDevice(filament_relay_pin)

desired_filament_current = 1.8 # Amps
max_filament_current = 1.80

ser = serial.Serial('/dev/ttyS0', 1000000, timeout=1)
#ser = serial.Serial('/dev/ttyUSB0', 1000000, timeout=1)

def get_filament_current():
    ser.write('?'.encode())
    return ser.readline().decode()

while True:
    print("Filament ON")
    filament.value = desired_filament_current / max_filament_current
    filament_relay.on()
    sleep(1)
    print(get_filament_current())

    sleep(3)

    print("Filament OFF")
    filament.value = 0.0
    filament_relay.off()
    sleep(1)
    print(get_filament_current())

    sleep(3)
