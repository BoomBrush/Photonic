import threading, subprocess, signal, ctypes
import socket, requests
import serial
import os
import time
import psutil

#from gpiozero import LED, PWMLED, Button
import gpiozero
from PIL import Image
from time import sleep
from io import BytesIO
from signal import pthread_kill, SIGTSTP
from ina219 import INA219, DeviceRangeError
import gphoto2 as gp

# Stepper motor steps for full rotation
FULL_ROTATION_STEPS = 3200

# Pins
CAMERA_SHUTTER_PIN = 25
CAMERA_POWER_PIN = 22

FILAMENT_MOSFET_PIN = 12
FILAMENT_RELAY_PIN = 23

HV_PRESENT_PIN = 5
HV_ACTIVE_PIN = 27
HV_PWM_PIN = 19

STEPPER_STEP_PIN = 20
STEPPER_DIRECTION_PIN = 21
STEPPER_ENABLE_PIN = 16

SWITCH_NETWORKS_PIN = 18

# Absolute limits / definitions
MAX_FILAMENT_CURRENT = 1.80
MAX_HV_POWER = 100
MAX_DURATION = 10000

FILAMENT_WAIT_TIME = 500
FILAMENT_VOLTAGE_THRESHOLD = 3.80
FILAMENT_POWER_THRESHOLD = 1.00

STEPPER_STEPS_PER_ROTATION = 200
STEPPER_SPEED = 0.001

CAMERA_TIMEOUT = 10
MAX_CAPTURE_ATTEMPTS = 3

HV_R1_RESISTANCE = 21_800
HV_R2_RESISTANCE = 70_750_000

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
            raise Exception("WARNING: No DSLR camera detected")

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

                print("Capture successful event set")
                self.capture_successful.set()
                self.capture_successful.clear()

        print("GPhoto2 thread stopping")

class power_monitor():
    def __init__(self, address, disabled=False):
        self.disabled = disabled

        if not disabled:
            self.ina = INA219(shunt_ohms = 0.1,
                              max_expected_amps = 3.0,
                              address = address,
                              busnum=1)

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


class Machine():
    def __init__(self, ignore_camera=False, skip_filament=False, keep_filament_on=False):
        # Class variables
        self.ignore_camera = ignore_camera
        self.skip_filament = skip_filament
        self.keep_filament_on = keep_filament_on

        # Kill other Python XRAY processes
        self.kill_other_python_processes()

        # INA219 Init
        try:
            self.filament_psu = power_monitor(0x40)
            self.hv_psu = power_monitor(0x41)
        except OSError:
            print("WARNING: INA219 ERROR")
            self.filament_psu = power_monitor(0x40, disabled=True)
            self.hv_psu = power_monitor(0x41, disabled=True)

        # GPIO Inits
        self.initialize_gpio()

        # Start camera thread and init DSLR
        if not self.ignore_camera:
            self.initialize_dslr()
            self.dslr.start()

        # HV PSU powered check
        if self.gpio_hv_present.value != 1:
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
        except Exception as e:
            print("Error:", e)
            print("Attempting to restart camera and try again")
            self.restart_camera()
            self.initialize_dslr()

    def initialize_gpio(self):
        self.gpio_hv_present = gpiozero.InputDevice(HV_PRESENT_PIN)
        self.gpio_hv_enable = gpiozero.OutputDevice(HV_ACTIVE_PIN)
        self.gpio_hv_pwm = gpiozero.PWMOutputDevice(HV_PWM_PIN)
        self.gpio_filament_mosfet = gpiozero.PWMOutputDevice(FILAMENT_MOSFET_PIN)
        self.gpio_filament_relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)
        self.gpio_camera_shutter = gpiozero.OutputDevice(CAMERA_SHUTTER_PIN)
        self.gpio_camera_power = gpiozero.OutputDevice(CAMERA_POWER_PIN)

        self.stepper_step = gpiozero.OutputDevice(STEPPER_STEP_PIN)
        self.stepper_direction = gpiozero.OutputDevice(STEPPER_DIRECTION_PIN)
        self.stepper_enable = gpiozero.OutputDevice(STEPPER_ENABLE_PIN)

        self.camera_shutter(False)
        self.gpio_camera_power.on()
        self.filament(False)
        self.hv(False)

        self.stepper_step.off()
        self.stepper_direction.off()
        self.stepper_enable.on()

    def system_check(self):
        # Filament
        print("Checking filament")
        if self.filament_psu.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
            print("FAIL: Filament voltage not present")
            return False

        self.filament(True)
        sleep(0.5)
        if self.filament_psu.power() < FILAMENT_POWER_THRESHOLD:
            print("FAIL: Filament no load")
            self.filament(False)
            return False

        self.filament(False)

        # HV
        print("Checking HV")
        if self.gpio_hv_present.value != 1:
            print("FAIL: HV PSU Not detected")
            return False

        self.hv(True, 0.5)
        sleep(0.25)

        vout = self.hv_psu.voltage()

        self.hv(False)

        high_voltage = self.calculate_hv(self.hv_psu.voltage())

        print(f"high_voltage={high_voltage}")

        # Camera
        for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
            print(f"Checking camera attempt {attempt}/{MAX_CAPTURE_ATTEMPTS}")

            self.camera_shutter(True)
            sleep(0.25)
            self.camera_shutter(False)

            if not self.ignore_camera:
                self.dslr.capture_successful.wait(timeout=CAMERA_TIMEOUT)

                if self.dslr.capture_filepath:
                    break
                else:
                    print("FAIL: DSLR Capture")

            if attempt == MAX_CAPTURE_ATTEMPTS:
                return False

        return True

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

        print(f"Capture started at {power}% waiting {duration}ms")

        hv_lowside = self.hv_psu.voltage()
        hv_highside = self.calculate_hv(hv_lowside)
        print(f"Before HV Lowside: {hv_lowside}, HV Highside: {hv_highside}")

        # Wait for filament to heat up
        if not self.skip_filament:
            self.filament(True, filament_current)
            sleep(FILAMENT_WAIT_TIME / 1000)
            print(f"Filament {self.filament_psu.current()}mA, {self.filament_psu.voltage()}V, {self.filament_psu.power()}mW")

        # Turn HV and camera on then wait
        self.hv(True, power / 100)

        if not self.ignore_camera:
            self.camera_shutter(True)

        # Wait for set duration
        sleep(duration / 1000)

        hv_lowside = self.hv_psu.voltage()
        hv_highside = self.calculate_hv(hv_lowside)
        print(f"After HV Lowside: {hv_lowside}, HV Highside: {hv_highside}")

        # Turn camera, HV and filament off
        self.camera_shutter(False)
        self.hv(False)

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
            return Image.open(self.dslr.capture_filepath)

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

    def hv(self, state, pwm=0):
        if pwm >= 0 and pwm <= 1:
            self.gpio_hv_pwm.value = pwm

            if state:
                self.gpio_hv_enable.on()
            else:
                self.gpio_hv_enable.off()
        else:
            print("PWM out of range")
            self.gpio_hv_pwm.value = 0

    def calculate_hv(self, vout):
        return vout + 50
#        return vout / (HV_R2_RESISTANCE / (HV_R1_RESISTANCE + HV_R2_RESISTANCE))

    def restart_camera(self):
        print("Restarting camera")
        self.gpio_camera_power.off()
        sleep(0.5)
        self.gpio_camera_power.on()
        sleep(2)

    def finished(self):
        if not self.ignore_camera:
            self.dslr.listening = False

        self.filament(False)
        self.hv(False)

        if not self.ignore_camera:
            self.camera_shutter(False)
            self.dslr.listening = False
