from time import sleep
import Photonic

XRAY = Photonic.Machine(ignore_camera=True)

print("Before filament current:", XRAY.filament_current())
print("Filament ON")
XRAY.filament(True)
sleep(5)

print("After filament current:", XRAY.filament_current())
print("Filament OFF")
XRAY.filament(False)

XRAY.kill()
