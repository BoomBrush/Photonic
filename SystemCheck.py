from time import sleep
import Photonic

XRAY = Photonic.Photonic()

if XRAY.system_check():
    print("System check passed!")
else:
    print("System check failed")

XRAY.finished()
