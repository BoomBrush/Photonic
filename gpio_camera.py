'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''

import RPi.GPIO as GPIO
from time import sleep

camera_pin = 4				# PWM pin connected to LED
GPIO.setwarnings(True)			#disable warnings
GPIO.setmode(GPIO.BCM)		#set pin numbering system
GPIO.setup(camera_pin,GPIO.OUT)

while True:
    GPIO.output(camera_pin, True)
    print("True")
    sleep(5)
    GPIO.output(camera_pin, False)
    print("False")
    sleep(5)



