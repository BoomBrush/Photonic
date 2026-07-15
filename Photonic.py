import threading, subprocess, signal
import socket, requests
import serial
import tinytuya
import atexit
import os

#from gpiozero import LED, PWMLED, Button
import gpiozero
from PIL import Image
from time import sleep
from io import BytesIO
from signal import pthread_kill, SIGTSTP

# Listening server
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 4444  # Port to listen on (non-privileged ports are > 1023)

# Stepper motor steps for full rotation
FULL_ROTATION_STEPS = 3200

# Pins
CAMERA_PIN = 4
FILAMENT_PIN = 18
FILAMENT_RELAY_PIN = 24
HV_PRESENT_PIN = 5
HV_ACTIVE_PIN = 22
HV_PWM_PIN = 19

MAX_FILAMENT_CURRENT = 1.80

class GPhoto(threading.Thread):
    def __init__(self):
        self.stdout = None
        self.stderr = None
        threading.Thread.__init__(self)

    def run(self):
        print("GPhoto2 thread running")
        self.p = subprocess.Popen(['gphoto2', '--capture-tethered', '--hook-script', 'gphoto_capture.sh', '--force-overwrite', '--filename', 'imgs/%Y-%m-%d-%H-%M-%S-%f.%C'],
                                  shell=False,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        self.stdout, self.stderr = self.p.communicate()

    def keepalive(self):
        return_code = self.p.returncode

        if return_code == None:
            print("Gphoto2 thread started")
        else:
            print(f"Gphoto2 thread has stopped with returncode {return_code}. Stopping...")
            exit()

    def existing_processes(self):
        tmp = os.popen("ps -Af").read()
        return tmp.count('gphoto2')

    def kill(self):
        pid = self.p.pid
        try:
            os.kill(pid, signal.SIGINT)
        except ProcessLookupError:
            print("Gphoto2 already killed")

class Machine():
    def __init__(self, ignore_camera=False):
        # Class variables
        self.ignore_camera = ignore_camera

        # DSLR Init
        self.dslr = GPhoto()

        # ESP32 init
        self.esp32_init()

        # GPIO Inits
        self.gpio_hv_present = gpiozero.InputDevice(HV_PRESENT_PIN)
        self.gpio_hv_enable = gpiozero.OutputDevice(HV_ACTIVE_PIN)
        self.gpio_hv_pwm = gpiozero.PWMOutputDevice(HV_PWM_PIN)
        self.gpio_filament = gpiozero.OutputDevice(FILAMENT_PIN)
        self.gpio_filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)
        self.gpio_camera = gpiozero.OutputDevice(CAMERA_PIN)

        self.camera(False)
        self.filament(False)
        self.hv_enable(False)
        self.hv_pwm(0)

        # HV PSU powered check
        if self.gpio_hv_present.value == 1:
            print("HV PSU Detected")
        else:
            print("WARNING: HV PSU NOT DETECTED")

        # DSLR thread check
        if not ignore_camera:
            self.dslr.start()
#            self.dslr.keepalive()

            # Defining cleanup function
            atexit.register(self.finished)

        # Filament monitor thread
        #self.filament_thread = threading.Thread(target=self.filament_monitor)

    def esp32_init(self):
        try:
            self.esp32_ser = serial.Serial('/dev/ttyS0', 1000000, timeout=1)
        except Exception as e:
            print("ESP32 failed to initialize:", e)
            return False

    def stepper_move(self, steps):
        pass
        #stepper_pos = str(int(FULL_ROTATION_STEPS / self.rotations) * steps) + ';'
        #self.arduino_ser.write(("STEPPER_MOVE:" + str(steps) + ";").encode())
        #print(f"Stepper moving to position {steps}")

    def stepper_enable(self, state):
        pass
        #self.arduino_ser.write(('STEPPER_ON;' if state else 'STEPPER_OFF;').encode())

    def capture(self, power, duration, filament_current=MAX_FILAMENT_CURRENT): # Power: 0-100%, Duration: ms
        # Wait for filament to heat up and for HV to sync with pwm
        self.hv_pwm(power / 100)
        self.filament(True, filament_current)
        sleep(1)
        print("Filament current:", self.filament_current())

        # Turn HV and camera on then wait
        print("Capture started. Waiting", duration, "ms")
        self.hv_enable(True)
        self.camera(True)
        sleep(duration / 1000)

        # Turn camera, HV and filament off
        self.camera(False)
        self.hv_enable(False)
        self.filament(False)
        self.hv_pwm(0)
        print("Filament current:", self.filament_current())

        # Return if ignoring camera
        if self.ignore_camera:
            print("Ignoring camera")
            return None

        # Get image from camera
        image_bytes = self.listen()

        if not image_bytes:
            return None

        image_filepath = image_bytes.decode()
        print(f"Recieved: {image_filepath}")

        img = Image.open(image_filepath)

        return img

    def filament(self, state, value=None):
        if state:
            self.gpio_filament_relay.on()

            if value:
                self.gpio_filament.value = float(value) / MAX_FILAMENT_CURRENT
            else:
                self.gpio_filament.value = 1.0
        else:
            self.gpio_filament.value = 0.0
            self.gpio_filament.off()
            self.gpio_filament_relay.off()

    def camera(self, state):
        self.gpio_camera.off() if state else self.gpio_camera.on()

    def hv_enable(self, state):
        self.gpio_hv_enable.on() if state else self.gpio_hv_enable.off()

    def hv_pwm(self, pwm):
        if pwm >= 0 and pwm <= 1:
            self.gpio_hv_pwm.value = pwm
        else:
            print("PWM out of range")
            self.gpio_hv_pwm.value = 0

    def filament_current(self):
        self.esp32_ser.write('?'.encode())
        try:
            line = self.esp32_ser.readline().decode('utf-8').rstrip()
            #current = float(line) * 0.00795412 - 15.24036691;
            current = float(line)

        except ValueError:
            print("SP32 Did not respond to filament current request")
            current = 0.0

        return current

    def finished(self):
        print("Finishing up...")
        self.filament(False)
        self.hv_enable(False)
        self.hv_pwm(0)

        if not self.ignore_camera:
            self.camera(False)
            print("Killing DSLR process")
            self.dslr.kill()
            print("Finished killing DSLR process")

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            print("Listening for camera image...")
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
