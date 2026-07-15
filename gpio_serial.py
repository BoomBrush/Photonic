import serial
from time import sleep

#ser = serial.Serial('/dev/ttyAMA0', 1000000, timeout=1)
ser = serial.Serial('/dev/ttyS0', 1000000, timeout=1)

while True:
    ser.write("?".encode())
    print(ser.readline().decode())
    sleep(0.5)
