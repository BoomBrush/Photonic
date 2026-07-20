from time import sleep
import Photonic

powers = [50, 60, 70]

XRAY = Photonic.Machine()

for p in powers:
    img = XRAY.capture(p, 2000)
    img.save(f"imgs/test image {p}.jpg")

XRAY.finished()
