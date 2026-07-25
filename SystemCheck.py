from time import sleep
import Photonic

XRAY = Photonic.Machine(ignore_camera=True)

if XRAY.system_check():
    print("System check passed!")
else:
    print("System check failed")

XRAY.finished()
