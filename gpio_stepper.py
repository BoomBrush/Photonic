import time
import gpiozero

step_pin = gpiozero.OutputDevice(21)
direction_pin = gpiozero.OutputDevice(20)
enable_pin = gpiozero.OutputDevice(16)

step_pin.off()
direction_pin.off()

steps_per_rotation = 200
steps = 20
speed = 0.01 # Lower is faster

def stepper(steps):
    direction_pin.on()
    for _ in range(steps):
        step_pin.on()
        time.sleep(speed)
        step_pin.off()
        time.sleep(speed)

enable_pin.off()

#for i in range(steps):
#    print("Turning", i)
#    turn = int(steps_per_rotation / steps)
stepper(200)

enable_pin.on()
