from time import sleep
import Photonic

POWER = 30
DURATION = 1000
NUMBER_OF_SCANS = 5

XRAY = Photonic.Machine()

for i in range(NUMBER_OF_SCANS):
    print("Scan", i + 1)
    img = XRAY.capture(POWER, DURATION)
    img.save("/home/boombrush/XRAY/imgs/" + str(i) + ".jpg")

    #XRAY.stepper_move(int(200 / NUMBER_OF_SCANS) * (i+1))

XRAY.finished()


#XRAY.startpos = 0
#XRAY.rotations = 5
#XRAY.scans = range(XRAY.startpos, XRAY.rotations + 1)


#for i in XRAY.scans:
#    repeat = True
#    while repeat:
#        print(f"Image {i} processing")
#        XRAY.stepper_move(i - XRAY.startpos)

#        try:
#            img = XRAY.capture(POWER, DURATION)
#        except Exception as e:
#            print("Xray exception - " + str(e))
#            img = False
#
#        if img:
#            img.save(f"imgs/test image {i}.jpg")
#            repeat = False
#        else:
#            print(f"Image {i} failed")

#        print("Waiting")
#        sleep(60)
