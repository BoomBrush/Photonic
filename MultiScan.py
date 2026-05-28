from time import sleep
import Photonic

POWER = 40
DURATION = 2000

XRAY = Photonic.Machine(using_stepper = True)

XRAY.startpos = 0
XRAY.rotations = 6
XRAY.scans = range(XRAY.startpos, XRAY.rotations + 1)
#XRAY.scans = [0, 2, 4, 7]

for i in XRAY.scans:
    repeat = True
    while repeat:
        print(f"Image {i} processing")
        XRAY.stepper_move(i - XRAY.startpos)

        try:
            img = XRAY.capture(POWER, DURATION)
        except Exception as e:
            print("Xray exception - " + str(e))
            img = False

        if img:
            img.save(f"imgs/test image {i}.jpg")
            repeat = False
        else:
            print(f"Image {i} failed")

        print("Waiting")
        sleep(60)

XRAY.stop()
