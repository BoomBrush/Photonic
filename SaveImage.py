from time import sleep
import Photonic, sys
import SystemCheck

XRAY = Photonic.Photonic()
SystemCheck.system_check(XRAY)

power = int(sys.argv[1])
duration = int(sys.argv[2])
filament_current = int(sys.argv[3])
filename = sys.argv[4]

img = XRAY.capture(power, duration, filament_current) # Power (%), Time (ms), Filament current (%)

if img:
    img.save(f"imgs/{filename}.jpg")
    print(f"Image saved as {filename}.jpg")
else:
    print("Image failed to be captured")

XRAY.finished()
