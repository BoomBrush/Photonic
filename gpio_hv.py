'''
Control the Brightness of LED using PWM on Raspberry Pi
http://www.electronicwings.com
'''

import RPi.GPIO as GPIO
from time import sleep

hv_pwm_pin = 13			# PWM pin connected to LED
hv_active_pin = 19

GPIO.setwarnings(True)			#disable warnings
GPIO.setmode(GPIO.BCM)		#set pin numbering system
GPIO.setup(hv_pwm_pin,GPIO.OUT)
GPIO.setup(hv_active_pin,GPIO.OUT)

hv_pwm = GPIO.PWM(hv_pwm_pin,1000)		#create PWM instance with frequency
hv_pwm.start(0)				#start PWM of required Duty Cycle 
hv_pwm.ChangeDutyCycle(20)

GPIO.output(hv_active_pin, True)

sleep(9999999)



