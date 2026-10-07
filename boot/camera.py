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

import gphoto2 as gp


class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.skip_system_check = False
        self.listening = True

    def run(self):
        self.camera = gp.Camera()
        camera_list = list(gp.Camera.autodetect())

        if len(camera_list) > 0:
            self.camera.init()
            print(camera_list[0][0], "initialized")
        else:
            raise Exception("No DSLR camera detected")

        address = ('127.0.0.1', 6000)
        listener = Listener(address, authkey=b'boombrush')

        while True:
           self.conn = listener.accept()
           print('connection accepted from', listener.last_accepted)

           while self.listening:
               print("Further listening attempt")
               msg = self.conn.recv()

               if msg == "skip":
                   self.conn.send(self.skip_system_check)
               elif msg == "close":
                   self.conn.close()
                   break
               elif msg == "image":
                   camera_capture_loop = True

                   while camera_capture_loop:
                       print("Waiting for image...")
                       event_type, event_data = self.camera.wait_for_event(1000)

                       if event_type == gp.GP_EVENT_FILE_ADDED:
                           cam_file = self.camera.file_get(event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                           target_path = os.path.join("imgs/raw", event_data.name)
                           cam_file.save(target_path)
                           print(target_path)

                           self.conn.send(target_path)
                           self.skip_system_check = True
                           sleep(1)

                           camera_capture_loop = False
                           os.remove("imgs/raw/" + event_data.name)
                           break

if __name__ == "__main__":
    dslr = Camera()
    dslr.start()
