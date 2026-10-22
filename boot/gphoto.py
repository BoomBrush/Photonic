
import threading, subprocess, signal, ctypes
import socket, requests
import serial
import os
import time
import psutil
import atexit

import gpiozero
from PIL import Image, ImageDraw, ImageFont
from time import sleep
from io import BytesIO
from signal import pthread_kill, SIGTSTP
from ina219 import INA219, DeviceRangeError
from multiprocessing.connection import Listener, Client
import Adafruit_MCP4725, Adafruit_ADS1x15
from subprocess import Popen, PIPE

import gphoto2 as gp


class gphoto2_init(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        process = Popen(['gphoto2', '--capture-tethered'])
        sleep(10)
        process.kill()


if __name__ == "__main__":
    init = gphoto2_init()
    init.start()
