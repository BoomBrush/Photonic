import time
import gpiozero

step_pin = gpiozero.OutputDevice(17)
direction_pin = gpiozero.OutputDevice(6)
enable_pin = gpiozero.OutputDevice(26)

step_pin.off()
direction_pin.off()

steps_per_rotation = 200
steps = 200
speed = 0.001 # Lower is faster

def stepper(steps):
    direction_pin.on()
    for _ in range(steps):
        step_pin.on()
        time.sleep(speed)
        step_pin.off()
        time.sleep(speed)

#enable_pin.off()

#for i in range(steps):
#    print("Turning", i)
#    turn = int(steps_per_rotation / steps)

while True:
    stepper(200)
    time.sleep(2)

#enable_pin.on()
