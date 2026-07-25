from time import sleep
import Photonic, sys
import numpy, cv2

XRAY = Photonic.Photonic()
#XRAY.system_check()

power = int(sys.argv[1])
duration = int(sys.argv[2])

img = XRAY.capture(power, duration) # Power (%), Time (ms), FilamentCurrent (Amps)

if img:
    #image = numpy.array(img)
    #greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #cv2.imwrite("imgs/remote.jpg", greyscale)

    img.save("imgs/remote.jpg")

    print("Done")
else:
    print("Image failed to be captured")

XRAY.finished()
