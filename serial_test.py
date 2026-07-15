from time import sleep
import Photonic

XRAY = Photonic.Machine(ignore_camera=True)

XRAY.ser.write("30%".encode())

print(XRAY.ser.readline())
