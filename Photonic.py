import threading, subprocess
import socket, requests
import serial
import tinytuya
import RPi.GPIO as GPIO
import atexit

from PIL import Image
from time import sleep
from io import BytesIO

# Listening server
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 4444  # Port to listen on (non-privileged ports are > 1023)

# Variables
FULL_ROTATION_STEPS = 3200

# Pins
CAMERA_PIN = 4
FILAMENT_PIN = 17
HV_ACTIVE_PIN = 19
HV_PWM_PIN = 13


class GPhoto(threading.Thread):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

    def run(self):
        self.p = subprocess.Popen(['gphoto2', '--capture-tethered', '--hook-script', 'gphoto_capture.sh', '--force-overwrite'],
                                  shell=False,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        self.stdout, self.stderr = self.p.communicate()

    def keepalive(self):
        return_code = self.p.returncode

        if return_code == None:
            print("Thread is still alive")
        else:
            print(f"Thread has stopped with returncode {return_code}. Stopping...")
            exit()


class Machine():
    def __init__(self, using_stepper=False):
        self.rotations = 0
        self.startpos = 0
        self.dslr = GPhoto()

        # DSLR Init
        self.dslr.start()
        sleep(1)
        print(f"GPhoto2 returncode is {self.dslr.p.returncode}")

        if self.dslr.p.returncode == 1:
            print("Is the camera plugged in and turned on?")

        self.dslr.keepalive()

        # Stepper Init
        if using_stepper:
            if self.stepper_init():
                print("Stepper motor ready")
            else:
                print("Stepper motor not ready")

        # GPIO Inits
        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(CAMERA_PIN, GPIO.OUT)
        GPIO.setup(FILAMENT_PIN, GPIO.OUT)
        GPIO.setup(HV_ACTIVE_PIN, GPIO.OUT)
        GPIO.setup(HV_PWM_PIN, GPIO.OUT)

        self.camera(False)
        self.filament(False)
        self.hv(False)

        self.HV_PWM = GPIO.PWM(HV_PWM_PIN, 1000)
        self.HV_PWM.start(0)
        self.hv_pwm(0)

        atexit.register(self.stop)

    def stepper_init(self):
        self.ser = serial.Serial('/dev/ttyACM0', 1000000, timeout=1)
        self.ser.reset_input_buffer()
        line = self.ser.readline().decode('utf-8').rstrip()
        if line == "Started":
            self.ser.write("!".encode())

    def stepper_move(self, i):
        stepper_pos = str(int(FULL_ROTATION_STEPS / self.rotations) * i) + ';'
        self.stepper_enable(True)
        self.ser.write(stepper_pos.encode())
        print(f"Stepper moving to {i}/{self.rotations} by {stepper_pos} steps")
        sleep(2)
        self.stepper_enable(False)

    def stepper_enable(self, state):
        self.ser.write(('!' if state else '*').encode())

    def capture(self, power, duration):
        # Wait for filament to heat up and for HV to sync with pwm
        self.hv_pwm(power)
        self.filament(True)
        sleep(2)

        # Turn camera and HV on then wait
        self.camera(True)
        self.hv(True)
        sleep(duration / 1000)

        # Turn camera, HV and filament off
        self.camera(False)
        self.hv(False)
        self.filament(False)
        self.hv_pwm(0)

        image_bytes = self.listen()

        if not image_bytes:
            return None

        image_filepath = image_bytes.decode()
        print(f"Recieved: {image_filepath}")

        img = Image.open(image_filepath)

        return img

    def filament(self, state):
        GPIO.output(FILAMENT_PIN, state)

    def camera(self, state):
        GPIO.output(CAMERA_PIN, not state)

    def hv(self, state):
        GPIO.output(HV_ACTIVE_PIN, state)

    def hv_pwm(self, pwm):
        self.HV_PWM.ChangeDutyCycle(pwm)

    def stop(self):
        print("Stopping...")
        self.dslr.p.kill()
        self.camera(False)
        self.filament(False)
        self.hv(False)
        self.hv_pwm(0)

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            print("Listening...")
            s.listen()
            try:
                conn, addr = s.accept()
            except TimeoutError:
                print("Timeout error")
                return None
            with conn:
                print(f"Connected by {addr}")

                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    break
        s.close()
        return data
