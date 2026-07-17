'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''

import gpiozero
from time import sleep
import serial

filament_mosfet_pin = 21				# PWM pin connected to LED
filament_relay_pin = 23

filament_mosfet = gpiozero.PWMOutputDevice(filament_mosfet_pin)
filament_relay = gpiozero.OutputDevice(filament_relay_pin)

desired_filament_current = 1.80 # Amps
max_filament_current = 1.80

ser = serial.Serial('/dev/ttyS0', 1000000, timeout=1)
#ser = serial.Serial('/dev/ttyUSB0', 1000000, timeout=1)

def get_filament_current():
    ser.write('?'.encode())

    print(ser.readall().decode())

while True:
    print("Filament ON")
    filament_mosfet.value = desired_filament_current / max_filament_current
    filament_relay.on()
    sleep(1)
    get_filament_current()

    sleep(3)

    print("Filament OFF")
    filament_mosfet.value = 0.0
    filament_relay.off()
    sleep(1)
    get_filament_current()

    sleep(3)
