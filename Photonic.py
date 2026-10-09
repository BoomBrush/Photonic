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

from LED import LED

# Pins
CAMERA_SHUTTER_PIN = 1
FILAMENT_RELAY_PIN = 0

HV_PRESENT_PIN = 9
HV_ACTIVE_PIN = 26
HV_PWM_PIN = 5

# I2C
I2C_BUS = 1
I2C_FILAMENT_ADDRESS = 0x40
I2C_HIGHVOLTAGE_ADDRESS = 0x41
I2C_ADC_ADDRESS = 0x48
I2C_DAC_ADDRESS_1 = 0x60
I2C_DAC_ADDRESS_2 = 0x61

# ADC VALUES
ADC_BIT_DEPTH = 32768
ADC_MAX_VOLTAGE_1 = 4.096
ADC_MAX_VOLTAGE_16 = 0.256
ADC_SAMPLES = 10
ADC_SMALLEST = ADC_MAX_VOLTAGE_16 / ADC_BIT_DEPTH
ADC_R1 = 80_000_000
ADC_R2 = 47 / 5
ADC_MAX = 4095

# Absolute limits / definitions
FILAMENT_WAIT_TIME = 2500
FILAMENT_VOLTAGE_THRESHOLD = 3.80
FILAMENT_CURRENT_THRESHOLD = 1.00

HV_VOLTAGE_THRESHOLD = 1000
CAMERA_TIMEOUT = 10
MAX_CAPTURE_ATTEMPTS = 3

KILL_PROCESS_EXCEPTIONS = ["http_server.py", "switch_wifi.py", "-m", "camera.py"]


class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.address = ('127.0.0.1', 6000)

        self.shutter = gpiozero.OutputDevice(CAMERA_SHUTTER_PIN)
        self.trigger(False)

        self.ready = threading.Event()
        self.skip_system_check = None

    def direct(self):
        print("Camera thread started")
        self.camera = gp.Camera()
        camera_list = list(gp.Camera.autodetect())

        if len(camera_list) > 0:
            self.camera.init()
            print(camera_list[0][0], "initialized")

            self.detected = True
        else:
            raise Exception("No DSLR camera detected")

        self.capture_filepath = None
        self.listening = True

        while self.listening:
            event_type, event_data = self.camera.wait_for_event(CAMERA_TIMEOUT * 1000)

            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = self.camera.file_get(event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join("imgs/raw", event_data.name)
                cam_file.save(target_path)

                self.capture_filepath = target_path
                self.ready.set()
                self.ready.clear()

        print("Camera thread stopping")

    def run(self):
        print("Camera thread started - server")

        self.listening = True
        self.capture_filepath = None
        self.ready.clear()

        if self.connect(self.address):
            self.conn_client.send("skip")
            msg = self.conn_client.recv()
            self.skip_system_check = msg
            self.conn_client.send("close")
            self.conn_client.close()

        if self.skip_system_check: return
        self.image()

    def trigger(self, state):
        if state:
            self.shutter.off()
        else:
            self.shutter.on()

    def connect(self, address):
        try:
            self.conn_client = Client(address, authkey=b'boombrush')
            return True
        except Exception as e:
            print("Could not connect to Photonic program:", e)

        return False

    def image(self):
        if self.connect(self.address):
            self.conn_client.send("image")
            print("Waiting for image from camera server")
            self.capture_filepath = self.conn_client.recv()
            print("Recieved image")
            self.conn_client.send("close")
            self.conn_client.close()
            self.ready.set()


class PowerMonitor():
    def __init__(self, address):
        self.disabled = False

        try:
            self.ina = INA219(shunt_ohms = 0.1,
                              max_expected_amps = 3.0,
                              address = address,
                              busnum=I2C_BUS)

            self.ina.configure(voltage_range=self.ina.RANGE_16V,
                               gain=self.ina.GAIN_AUTO,
                               bus_adc=self.ina.ADC_128SAMP,
                               shunt_adc=self.ina.ADC_128SAMP)

        except OSError:
            raise Exception("WARNING: INA219 ERROR")
            self.disabled = True

    def current(self):
        if self.disabled: return 0.0

        try:
            return int(self.ina.current())
        except DeviceRangeError:
            raise Exception("INA219 current range error")

    def voltage(self):
        if self.disabled: return 0.0

        return self.ina.voltage()

    def power(self):
        if self.disabled: return 0.0

        try:
            return int(self.ina.power())
        except DeviceRangeError:
            raise Exception("INA219 power range error")


class ADS1115():
    def __init__(self):
        self.ads1115 = Adafruit_ADS1x15.ADS1115(address=I2C_ADC_ADDRESS, busnum=I2C_BUS)

    def average(self, channel, gain):
        sum = 0

        for _ in range(ADC_SAMPLES):
            sum += self.ads1115.read_adc(channel, gain=gain)

        return sum / ADC_SAMPLES


class Filament(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.relay = gpiozero.OutputDevice(FILAMENT_RELAY_PIN)

        try:
            self.dac = Adafruit_MCP4725.MCP4725(busnum=1, address=I2C_DAC_ADDRESS_1)
            self.dac.set_voltage(0)
        except OSError:
            self.dac = Adafruit_MCP4725.MCP4725(busnum=1, address=I2C_DAC_ADDRESS_2)
            self.dac.set_voltage(0)

        self.power = PowerMonitor(I2C_FILAMENT_ADDRESS)

        self.enable = threading.Event()
        self.current = 0

    def run(self):
        print("Filament thread started")

        while True:
            while self.enable.is_set():
                self.set(True, estimated_current_value)

                current = self.power.current()
                print("Actual Current:", current, "Estimated current value:", estimated_current_value)

            sleep(0.1)
        print("Filament thread stopped")

    def set(self, state, value = ADC_MAX):
        if value <= ADC_MAX and value >= 0:
            if state:
                self.relay.on()
                self.dac.set_voltage(int(value))
            else:
                self.relay.off()
                self.dac.set_voltage(0)
        else:
            print("ADC value out of range")
            self.relay.off()
            self.dac.set_voltage(0)

    def mosfet_voltage(self, adc_value):
        return round((adc_value / ADC_BIT_DEPTH) * ADC_MAX_VOLTAGE_1, 3)


class HighVoltage():
    def __init__(self):
        self.present = gpiozero.InputDevice(HV_PRESENT_PIN)
        self.enable = gpiozero.OutputDevice(HV_ACTIVE_PIN)
        self.pwm = gpiozero.PWMOutputDevice(HV_PWM_PIN)

        self.power = PowerMonitor(I2C_HIGHVOLTAGE_ADDRESS)

    def set(self, pwm):
        if pwm >= 0 and pwm <= 1:
            self.pwm.value = pwm

            if pwm == 0:
                self.enable.off()
            else:
                self.enable.on()
        else:
            print("PWM out of range")
            self.pwm.value = 0

    def calculate(self):
        return round(self.power.voltage() / (ADC_R2 / (ADC_R1 + ADC_R2)) / 1_000_000, 3)

    #def current(self. adc_0_before, adc_1_before):
        #print(f"before_0:{before_0},after_0:{after_0},before_1:{before_1},after_1:{after_1}")
        #delta_0 = abs(before_0 - after_0)
        #delta_1 = abs(before_1 - after_1)
        #delta = abs(delta_0 - delta_1)
        #return (delta / ADC_BIT_DEPTH) * ADC_MAX_VOLTAGE_16

        #adc_0_after = self.adc.average(0, 16)
        #adc_1_after = self.adc.average(1, 16)
        #return round(self.calculate_hv_current(adc_0_before, adc_0_after, adc_1_before, adc_1_after) * 1000, 3)

    def estimate(self, filament_current):
       return round(5.20593227*10**-7 * 8814.52450668**(filament_current/1000), 3)


class FilamentInterpolation():
    def __init__(self, filename):
        with open(filename,'rb') as file:
            self.lines = file.readlines()
            self.dacs = []
            self.currents = []

        for line in self.lines:
            row = line.decode().split(" ")

            current_value = float(row[0])
            dac_value = float(row[1][:-1])

            self.dacs.append(dac_value)
            self.currents.append(current_value)

    def dac_to_current(self, value):
        for i in list(range(len(self.dacs))):
            dac = self.dacs[i]

            if dac > value:
                return (self.currents[i] + self.currents[i-1]) / 2

    def current_to_dac(self, value):
        for i in list(range(len(self.currents))):
            current = self.currents[i]

            if self.currents[i] > value:
                return (self.dacs[i] + self.dacs[i-1]) / 2


class Photonic():
    def __init__(self, ignore_exceptions=False, disable_led=False):
        # At exit functions
        self.finished = False
        atexit.register(self.finish)
        signal.signal(signal.SIGTERM, self.finish)
        signal.signal(signal.SIGINT, self.finish)

        # Kill other Python XRAY processes
        self.manage_python_processes()

        # Class variables
        self.ignore_exceptions = ignore_exceptions
        self.capture_attempts = 0
        self.disable_led = disable_led

        # ADS1115, Filament, HV, LED, interpolate init
        self.adc = ADS1115()
        self.filament = Filament()
        self.hv = HighVoltage()
        self.led = LED()
        self.interpolate = FilamentInterpolation("assets//filament_currents.csv")


        # DSLR init
        try:
            self.dslr = Camera()
            self.dslr.start()
        except Exception as e:
            print("DSLR Error:", e)

        #self.dslr.ready.wait(CAMERA_TIMEOUT)

        # DSLR check
        #if not self.dslr.detected:
        #    if not ignore_exceptions: raise Exception("WARNING: DSLR NOT INITIALIZED")
        #    else: print("WARNING: DSLR NOT INITIALIZED")

        # HV PSU powered check
        if self.hv.present.value != 1:
            if not ignore_exceptions: raise Exception("WARNING: HV PSU NOT DETECTED")
            else: print("WARNING: HV PSU NOT DETECTED")

        # Filament power check
        if self.filament.power.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
            if not ignore_exceptions: raise Exception("WARNING: NO POWER TO FILAMENT")
            else: print("WARNING: NO POWER TO FILAMENT")

    def capture(self, power, duration, filament_power = ADC_MAX):
        self.capture_attempts += 1

        # LED to yellow
        if not self.disable_led: self.led.set(1, 1)

        # Grab values before capture
        adc_0_before = self.adc.average(0, 16)
        adc_1_before = self.adc.average(1, 16)

        # Wait for filament to heat up
        self.filament.set(True, filament_power)
        sleep(FILAMENT_WAIT_TIME / 1000)

        # Turn HV and camera on then wait
        self.hv.set(power / 100)
        self.dslr.trigger(True)

        # LED to red
        if not self.disable_led: self.led.set(1, 0)

        # Wait for set period
        sleep((duration / 1000) / 2)

        # get filament current
        filament_current = self.filament.power.current()

        # MOSFET voltage
        mosfet_voltage = self.filament.mosfet_voltage(self.adc.average(3, 1))

        # Get hv current and voltage
        hv_current_estimate = self.hv.estimate(filament_current)
        hv_voltage = self.hv.calculate()

        # Wait for set duration minus already elapsed time
        capture_settings = f"{power}% {duration}ms {int(filament_current)}mA ~ {filament_power} {mosfet_voltage}V ~ E{hv_current_estimate}mA {hv_voltage}kV"
        print(f"Capture started:", capture_settings)
        sleep((duration / 1000) / 2)

        # Turn camera, HV and filament off
        self.dslr.trigger(False)
        self.hv.set(0)
        self.filament.set(False)

        # LED to yellow
        if not self.disable_led: self.led.set(1, 1)

        # If camera not present, return
        #if not self.dslr.detected: return False

        # Get image from camera
        print("Waiting for camera capture event")
        self.dslr.image()
        self.dslr.ready.wait(timeout=CAMERA_TIMEOUT)

        if self.dslr.capture_filepath:
            print("Recieved image from camera")
            self.dslr.listening = False
            self.capture_attempts = 0
            # LED to green
            if not self.disable_led: self.led.set(0, 1, turn_off_period = 10)

            # Add parameters as text at top left of picture
            img = Image.open(self.dslr.capture_filepath)
            image_draw = ImageDraw.Draw(img)
            image_font = ImageFont.truetype("ARIAL.TTF", 36)
            image_draw.text((40, 40), capture_settings, fill=(255, 255, 255), font=image_font)

            self.capture_attempts = 0
            return img

        print("Did not receive capture after timeout period. Retrying...")

        if self.capture_attempts < MAX_CAPTURE_ATTEMPTS: return self.capture(power, duration)

        # Reached max capture attempts
        print("Maximum capture attempts reached")
        if not self.disable_led: self.led.set(0, 0)
        return None

    def manage_python_processes(self):
        current_pid = os.getpid()
        camera_script_running = False

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

                    if filename == "camera.py":
                        camera_script_running = True

        if not camera_script_running:
            pass
            #print("Running camera script")
            #subprocess.run(["python", "/home/boombrush/Photonic/boot/camera.py", "&"], shell=False)
            #print("Now running camera script")

    # Cleanup method to make sure controls are gracefully stopped
    def finish(self):
        if self.finished: return False
        print("Exiting...")

        try:
            self.dslr.listening = False
            self.filament.set(False)
            self.hv.set(0)
            self.dslr.trigger(False)
            self.finished = True
        except Exception:
            print("Exception in finish method!")

