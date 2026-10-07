from time import sleep
import gpiozero


PWM_PIN = 24


pwm = gpiozero.PWMOutputDevice(PWM_PIN)

while True:
    print("PWM ON")
    pwm.value = 1.0
    sleep(2)
    print("PWM OFF")
    pwm.value = 0.0
    sleep(2)

