'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''

import RPi.GPIO as GPIO
from time import sleep

pin = 17				# PWM pin connected to LED
GPIO.setwarnings(True)			#disable warnings
GPIO.setmode(GPIO.BCM)		#set pin numbering system
GPIO.setup(pin,GPIO.OUT)

while True:
    GPIO.output(pin, True)
    print("True")
    sleep(5)
    GPIO.output(pin, False)
    print("False")
    sleep(5)



