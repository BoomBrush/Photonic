import threading, subprocess, signal, ctypes
import http.server, socketserver
import socket, requests
import serial
import tinytuya
import atexit
import os
import time
import psutil

#from gpiozero import LED, PWMLED, Button
import gpiozero
from PIL import Image
from time import sleep
from io import BytesIO
from signal import pthread_kill, SIGTSTP
import gphoto2 as gp

# Stepper motor steps for full rotation
FULL_ROTATION_STEPS = 3200

# Pins
CAMERA_SHUTTER_PIN = 4
CAMERA_POWER_PIN = 27
FILAMENT_MOSFET_PIN = 12
FILAMENT_RELAY_PIN = 23
HV_PRESENT_PIN = 5
HV_ACTIVE_PIN = 17
HV_PWM_PIN = 19
STEPPER_STEP_PIN = 21
STEPPER_DIRECTION_PIN = 20
STEPPER_ENABLE_PIN = 16

# Absolute limits
MAX_FILAMENT_CURRENT = 1.80
MAX_HV_POWER = 50
MAX_DURATION = 5000
FILAMENT_WAIT_TIME = 100
STEPPER_STEPS_PER_ROTATION = 200
STEPPER_SPEED = 0.001
CAMERA_TIMEOUT = 10

class GPhoto(threading.Thread):
    def __init__(self, disable_timeout=False):
        threading.Thread.__init__(self)
        self.disable_timeout = disable_timeout
        self.camera = gp.Camera()
        self.camera_detected = False

        camera_list = list(gp.Camera.autodetect())

        if len(camera_list) > 0:
            self.camera.init()
            print(camera_list[0][0], "initialized")

            self.camera_detected = True
            self.running = True
        else:
            raise Exception("WARNING: No DSLR camera detected")

        self.capture_successful = threading.Event()
        self.capture_filepath = None
        self.timeout = 1000

    def run(self):
        print("GPhoto2 thread running and waiting for image...")
        start_time = time.time()
        self.listening = True

        while self.listening:
            self.capture_successful.clear()

            event_type, event_data = self.camera.wait_for_event(self.timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = self.camera.file_get(event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join("/home/boombrush/XRAY/imgs/raw", event_data.name)
                cam_file.save(target_path)
                self.capture_filepath = target_path
                self.capture_successful.set()

            #if (start_time + CAMERA_TIMEOUT) > time.time():
            #    self.capture_done.set()


        # Release main thread upon timing out and no picture is taken
#        if not self.capture_done.is_set():
#            print("Gphoto2 thread timed out")
#            self.capture_done.set()

    def kill(self):
        print("Ending gphoto2 thread")
        self.running = False


class Machine():
    def __init__(self, ignore_camera=False, skip_filament=False, disable_timeout=False):
        # Class variables
        self.ignore_camera = ignore_camera
        self.skip_filament = skip_filament
        self.disable_timeout = disable_timeout
        self.http_server_process = None

        # Kill other Python XRAY processes
        self.kill_other_python_processes()

        # GPIO Inits
        try:
            self.initialize_gpio()
        except Exception as e:
            print("Error:", e)
            exit()

        # DSLR Init
        self.initialize_dslr()

        # Start camera thread
        if not self.ignore_camera:
            self.dslr.start()

        # ESP32 init
        self.esp32_init()

        # HV PSU powered check
        if self.gpio_hv_present.value == 1:
            print("HV PSU Detected")
        else:
            print("WARNING: HV PSU NOT DETECTED")

    def kill_other_python_processes(self):
        current_pid = os.getpid()

        for process_id in psutil.pids():
            if process_id == current_pid: continue

            try:
                p = psutil.Process(process_id)
            except psutil.NoSuchProcess:
                continue

            if p.name() == "python":
                cmd_line = p.cmdline()

                if 'http_server' not in cmd_line[1]:
                    print("Killing XRAY script:", cmd_line)
                    p.kill()

    def initialize_dslr(self):
        if not self.ignore_camera:
            try:
                self.dslr = GPhoto(disable_timeout=self.disable_timeout)
            except Exception as e:
                print("Error:", e)
                print("Attempting to restart camera and try again")
                self.restart_camera()
                self.initialize_dslr()

    def initialize_gpio(self):
        self.gpio_hv_present = gpiozero.InputDevice(HV_PRESENT_PIN)
        self.gpio_hv_enable = gpiozero.OutputDevice(HV_ACTIVE_PIN)
        self.gpio_hv_pwm = gpiozero.PWMOutputDevice(HV_PWM_PIN)
        self.gpio_filament_mosfet = gpiozero.OutputDevice(FILAMENT_MOSFET_PIN)
        self.gpio_filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)
        self.gpio_camera_shutter = gpiozero.OutputDevice(CAMERA_SHUTTER_PIN)
        self.gpio_camera_power = gpiozero.OutputDevice(CAMERA_POWER_PIN)

        self.stepper_step = gpiozero.OutputDevice(STEPPER_STEP_PIN)
        self.stepper_direction = gpiozero.OutputDevice(STEPPER_DIRECTION_PIN)
        self.stepper_enable = gpiozero.OutputDevice(STEPPER_ENABLE_PIN)

        self.camera_shutter(False)
        self.gpio_camera_power.on()
        self.filament(False)
        self.hv_enable(False)
        self.hv_pwm(0)

        self.stepper_step.off()
        self.stepper_direction.off()
        self.stepper_enable.on()

    def esp32_init(self):
        try:
            self.esp32_ser = serial.Serial('/dev/ttyS0', 1000000, timeout=1)
        except Exception as e:
            print("ESP32 failed to initialize:", e)
            return False

    def stepper_move(self, steps):
        self.stepper_enable.off()

        for _ in range(steps):
            self.stepper_step.on()
            sleep(STEPPER_SPEED)
            self.stepper_step.off()
            sleep(STEPPER_SPEED)

        self.stepper_enable.on()

    def capture(self, power, duration, filament_current=MAX_FILAMENT_CURRENT):
        # Enforce absolute limits
        if power > MAX_HV_POWER: power = MAX_HV_POWER
        if duration > MAX_DURATION: duration = MAX_DURATION
        if filament_current > MAX_FILAMENT_CURRENT: filament_current = MAX_FILAMENT_CURRENT

        # Wait for filament to heat up and for HV to sync with pwm
        self.hv_pwm(power / 100)
        if not self.skip_filament:
            self.filament(True, filament_current)
            sleep(FILAMENT_WAIT_TIME / 1000)

        print("Filament current:", self.filament_current() / 1000, "amps")

        # Turn HV and camera on then wait
        self.hv_enable(True)
        if not self.ignore_camera:
            self.camera_shutter(True)
        print("Capture started. Waiting", duration, "ms")
        sleep(duration / 1000)

        # Turn camera, HV and filament off
        self.camera_shutter(False)
        self.hv_enable(False)
        self.filament(False)
        self.hv_pwm(0)

        # Return if ignoring camera
        if self.ignore_camera:
            print("Ignoring camera")
            return None
        elif not self.dslr.camera_detected:
            return None

        # Get image from camera
        print("Waiting for camera capture event")
        self.dslr.capture_successful.wait(timeout=5)
        print("Recieved camera capture")

        #if not self.dslr.capture_successful.is_set():
        #    return None

        #self.dslr.capture_successful.clear()

        img = Image.open(self.dslr.capture_filepath)
        return img

    def filament(self, state, value=None):
        if state:
            self.gpio_filament_relay.on()

            if value:
                self.gpio_filament_mosfet.value = float(value) / MAX_FILAMENT_CURRENT
            else:
                self.gpio_filament_mosfet.value = 1.0
        else:
            self.gpio_filament_mosfet.value = 0.0
            self.gpio_filament_mosfet.off()
            self.gpio_filament_relay.off()

    def camera_shutter(self, state):
        self.gpio_camera_shutter.off() if state else self.gpio_camera_shutter.on()

    def hv_enable(self, state):
        self.gpio_hv_enable.on() if state else self.gpio_hv_enable.off()

    def hv_pwm(self, pwm):
        if pwm >= 0 and pwm <= 1:
            self.gpio_hv_pwm.value = pwm
        else:
            print("PWM out of range")
            self.gpio_hv_pwm.value = 0

    def filament_current(self):
        output = ""
        self.esp32_ser.write('?'.encode())
        try:
            while True:
                line = self.esp32_ser.readline().decode('utf-8').rstrip()
                print(line)
                if line == "":
                    break

            #current = float(line) * 0.00795412 - 15.24036691;
            #current = float(line)
            return 0.0

        except ValueError:
            print("SP32 Did not respond to filament current request")
            current = 0.0

        #return None

    def restart_camera(self):
        self.gpio_camera_power.off()
        sleep(0.5)
        self.gpio_camera_power.on()
        sleep(5)

    def http_server(self, port=8000, keepalive=False):
        self.http_server_process = HTTP_Server(port, keepalive)
        self.http_server_process.start()

    def finished(self):
        self.dslr.listening = False
        self.filament(False)
        self.hv_enable(False)
        self.hv_pwm(0)

        if not self.ignore_camera:
            self.camera_shutter(False)
            self.dslr.kill()

        print("Exiting")

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
