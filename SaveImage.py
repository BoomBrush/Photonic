from time import sleep
import Photonic, sys

XRAY = Photonic.Photonic()

filename = sys.argv[1]
power = int(sys.argv[2])
duration = int(sys.argv[3])

img = XRAY.capture(power, duration) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    img.save(f"imgs/{filename}.jpg")
else:
    print("Image failed to be captured")

XRAY.finished()
