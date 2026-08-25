import threading, subprocess, signal, ctypes
import socket, requests
import serial
import os
import time
import psutil

import gpiozero
from PIL import Image, ImageDraw, ImageFont
from time import sleep
from io import BytesIO
from signal import pthread_kill, SIGTSTP
from ina219 import INA219, DeviceRangeError

import gphoto2 as gp

from LED import LED

# Pins
CAMERA_SHUTTER_PIN = 25

FILAMENT_MOSFET_PIN = 18
FILAMENT_RELAY_PIN = 23

HV_POWER_PIN = 0
HV_ACTIVE_PIN = 26
HV_PWM_PIN = 13

#STEPPER_STEP_PIN = 17
#STEPPER_DIRECTION_PIN = 6
#STEPPER_ENABLE_PIN = 26

# Absolute limits / definitions
MAX_FILAMENT_CURRENT = 2.0
MAX_HV_POWER = 100
MAX_DURATION = 10000

FILAMENT_WAIT_TIME = 500
FILAMENT_VOLTAGE_THRESHOLD = 3.80
FILAMENT_POWER_THRESHOLD = 1.00

HV_VOLTAGE_THRESHOLD = 1000

#STEPPER_STEPS_PER_ROTATION = 200
#STEPPER_SPEED = 0.001

CAMERA_TIMEOUT = 10
MAX_CAPTURE_ATTEMPTS = 3

HV_R1_RESISTANCE = 70_750_000
HV_R2_RESISTANCE = 21_800

KILL_PROCESS_EXCEPTIONS = ["http_server.py", "switch_wifi.py"]


class GPhoto2(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.camera = gp.Camera()
        self.camera_detected = False

        camera_list = list(gp.Camera.autodetect())

        if len(camera_list) > 0:
            self.camera.init()
            print(camera_list[0][0], "initialized")

            self.camera_detected = True
        else:
            raise Exception("No DSLR camera detected")

        self.capture_successful = threading.Event()
        self.capture_filepath = None
        self.timeout = CAMERA_TIMEOUT * 1000

    def run(self):
        print("GPhoto2 thread started")
        self.listening = True

        while self.listening:
            event_type, event_data = self.camera.wait_for_event(self.timeout)

            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = self.camera.file_get(event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join("imgs/raw", event_data.name)
                cam_file.save(target_path)
                self.capture_filepath = target_path

                self.capture_successful.set()
                self.capture_successful.clear()

        print("GPhoto2 thread stopping")

class PowerMonitor():
    def __init__(self, address, disabled=False):
        self.disabled = disabled

        if not disabled:
            self.ina = INA219(shunt_ohms = 0.1,
                              max_expected_amps = 3.0,
                              address = address,
                              busnum=2)

            self.ina.configure(voltage_range=self.ina.RANGE_16V,
                               gain=self.ina.GAIN_AUTO,
                               bus_adc=self.ina.ADC_128SAMP,
                               shunt_adc=self.ina.ADC_128SAMP)

    def current(self):
        if self.disabled: return 0.0

        try:
            if self.ina.power() == 0.0:
                return 0.0

            return int(self.ina.current())
        except DeviceRangeError:
            return self.current()

    def voltage(self):
        if self.disabled: return 0.0

        return self.ina.voltage()

    def power(self):
        if self.disabled: return 0.0

        try:
            return int(self.ina.power())
        except DeviceRangeError:
            return int(self.power())


class Photonic():
    def __init__(self, ignore_camera=False, skip_filament=False, keep_filament_on=False):
        # Class variables
        self.ignore_camera = ignore_camera
        self.skip_filament = skip_filament
        self.keep_filament_on = keep_filament_on
        self.status_led = LED()

        # GPIO Inits
        self.initialize_gpio()

        # Kill other Python XRAY processes
        self.kill_other_python_processes()

        # INA219 Init
        try:
            self.filament_psu = PowerMonitor(0x40)
            self.hv_highside = PowerMonitor(0x41)
            self.hv_lowside = PowerMonitor(0x44)
        except OSError:
            print("WARNING: INA219 ERROR")
            self.filament_psu = PowerMonitor(0x40, disabled=True)
            self.hv_highside = PowerMonitor(0x41, disabled=True)
            self.hv_lowside = PowerMonitor(0x44, disabled=True)

        # Start camera thread and init DSLR
        if not self.ignore_camera:
            self.initialize_dslr()

        # HV PSU powered check
        if self.gpio_hv_power.value != 1:
            print("WARNING: HV PSU NOT DETECTED")

        # Filament power check
        if self.filament_psu.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
            print("WARNING: NO POWER TO FILAMENT")

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

                if len(cmd_line) > 1:
                    filename = cmd_line[1].split("/")[-1]

                    if filename not in KILL_PROCESS_EXCEPTIONS:
                        print("Killing script:", ' '.join(cmd_line))
                        p.kill()

    def initialize_dslr(self):
        try:
            self.dslr = GPhoto2()
            self.dslr.start()
        except Exception as e:
            print("DSLR Error:", e)
            self.ignore_camera = True

    def initialize_gpio(self):
        self.gpio_hv_power = gpiozero.InputDevice(HV_POWER_PIN)
        self.gpio_hv_enable = gpiozero.OutputDevice(HV_ACTIVE_PIN)
        self.gpio_hv_pwm = gpiozero.PWMOutputDevice(HV_PWM_PIN)
        self.gpio_filament_mosfet = gpiozero.PWMOutputDevice(FILAMENT_MOSFET_PIN)
        self.gpio_filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)
        self.gpio_camera_shutter = gpiozero.OutputDevice(CAMERA_SHUTTER_PIN)
        #self.stepper_step = gpiozero.OutputDevice(STEPPER_STEP_PIN)
        #self.stepper_direction = gpiozero.OutputDevice(STEPPER_DIRECTION_PIN)
        #self.stepper_enable = gpiozero.OutputDevice(STEPPER_ENABLE_PIN)

        self.camera_shutter(False)
        self.filament(False)
        self.hv(0)

        #self.stepper_step.off()
        #self.stepper_direction.off()
        #self.stepper_enable.on()

#    def stepper_move(self, steps):
#        self.stepper_enable.off()
#
#        for _ in range(steps):
#            self.stepper_step.on()
#            sleep(STEPPER_SPEED)
#            self.stepper_step.off()
#            sleep(STEPPER_SPEED)
#
#        self.stepper_enable.on()

    def capture(self, power, duration, filament_current=MAX_FILAMENT_CURRENT):
        # Enforce absolute limits
        if power > MAX_HV_POWER: power = MAX_HV_POWER
        if duration > MAX_DURATION: duration = MAX_DURATION
        if filament_current > MAX_FILAMENT_CURRENT: filament_current = MAX_FILAMENT_CURRENT

        # Set LED to red
        self.led(1, 0, 0)

        # Wait for filament to heat up
        if not self.skip_filament:
            self.filament(True, filament_current)
            sleep(FILAMENT_WAIT_TIME / 1000)
            #print(f"Filament {self.filament_psu.current()}mA, {self.filament_psu.voltage()}V, {self.filament_psu.power()}mW")

        # Turn HV and camera on then wait
        self.hv(power / 100)

        if not self.ignore_camera:
            self.camera_shutter(True)

        hv_voltage = int(round(self.calculate_hv(self.hv_highside.voltage()) / 1000, 0))
        hv_current = self.hv_lowside.current()
        capture_settings = f"{power}% {duration}ms {self.filament_psu.current()}mA/{filament_current}A {hv_voltage}kV {hv_current}mA"

        # Wait for set duration
        print(f"Capture started:", capture_settings)
        sleep(duration / 1000)

        # Turn camera, HV and filament off
        self.camera_shutter(False)
        self.hv(0)
        self.led(1, 1, 0)

        if not self.keep_filament_on:
            self.filament(False)
            sleep(FILAMENT_WAIT_TIME / 1000)

        # Return if ignoring camera
        if self.ignore_camera:
            print("Ignoring camera")
            return None
        elif not self.dslr.camera_detected:
            return None

        # Get image from camera
        print("Waiting for camera capture event")
        self.dslr.capture_successful.wait(timeout=CAMERA_TIMEOUT)

        if self.dslr.capture_filepath:
            print("Recieved image from camera")
            # Set LED to green
            self.led(0, 1, 0, turn_off_period = 10)

            img = Image.open(self.dslr.capture_filepath)

            image_draw = ImageDraw.Draw(img)
            image_font = ImageFont.truetype("ARIAL.TTF", 36)

            image_draw.text((40, 40), capture_settings, fill=(255, 255, 255), font=image_font)

            return img

        print("Did not receive capture after timeout period. Retrying...")

        return self.capture(power, duration, filament_current)

    def filament(self, state, value=MAX_FILAMENT_CURRENT):
        if state:
            self.gpio_filament_mosfet.value = float(value) / MAX_FILAMENT_CURRENT
            self.gpio_filament_relay.on()
        else:
            self.gpio_filament_mosfet.value = 0.0
            self.gpio_filament_relay.off()

    def camera_shutter(self, state):
        if state:
            self.gpio_camera_shutter.off()
        else:
            self.gpio_camera_shutter.on()

    def led(self, r, g, b, turn_off_period=0, blink=False):
        try:
            self.status_led.connect()
            self.status_led.set(r, g, b, turn_off_period)
            self.status_led.disconnect()
        except ConnectionRefusedError:
            print("WARNING: LED connection refused")

    def hv(self, pwm):
        if pwm >= 0 and pwm <= 1:
            self.gpio_hv_pwm.value = pwm

            if pwm == 0:
                self.gpio_hv_enable.off()
            else:
                self.gpio_hv_enable.on()
        else:
            print("PWM out of range")
            self.gpio_hv_pwm.value = 0

    def calculate_hv(self, vout):
        return vout / (HV_R2_RESISTANCE / (HV_R1_RESISTANCE + HV_R2_RESISTANCE))

    def finished(self):
        if not self.ignore_camera:
            self.dslr.listening = False

        self.filament(False)
        self.hv(0)

        if not self.ignore_camera:
            self.camera_shutter(False)
            self.dslr.listening = False
