import gpiozero
from time import sleep

STATUS_LED_PIN = 23

status_led = gpiozero.PWMOutputDevice(STATUS_LED_PIN)

while True:
    print("LED ON")
    status_led.value = 1.0
    sleep(1)
    print("LED OFF")
    status_led.value = 0.0
    sleep(1)
