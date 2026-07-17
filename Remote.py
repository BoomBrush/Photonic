from time import sleep
import Photonic, sys

XRAY = Photonic.Machine()

power = int(sys.argv[1])
duration = int(sys.argv[2])

img = XRAY.capture(power, duration) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    img.save("/home/boombrush/XRAY/imgs/remote.jpg")
    print("Done")
else:
    print("Image failed to be captured")

XRAY.finished()
