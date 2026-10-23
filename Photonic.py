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

from LED import LED, Flashing

# Pins
CAMERA_SHUTTER_PIN = 25
FILAMENT_RELAY_PIN = 0

HV_PRESENT_PIN = 9
HV_ENABLE_PIN = 19
HV_PWM_PIN = 13

# I2C
I2C_BUS = 1
I2C_HIGHVOLTAGE_ADDRESS = 0x40
I2C_FILAMENT_ADDRESS = 0x41
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
ADC_R2 = 4670
ADC_R_VDROP = 47 / 5
ADC_MAX = 4095

# Absolute limits / definitions
FILAMENT_WAIT_TIME = 2500
FILAMENT_VOLTAGE_THRESHOLD = 3.80
FILAMENT_CURRENT_THRESHOLD = 1.00

HV_VOLTAGE_THRESHOLD = 1000
CAMERA_TIMEOUT = 10
MAX_CAPTURE_ATTEMPTS = 5

KILL_PROCESS_EXCEPTIONS = ["http_server.py", "switch_wifi.py", "-m", "camera.py"]
INTERPOLATE_FILEPATH = "assets//filament_currents.csv"

# Direct / Remote capture options
DIRECT_CAPTURE = False
REMOTE_CAPTURE = True


class Camera(threading.Thread):
    def __init__(self, capture_method):
        threading.Thread.__init__(self)
        self.address = ('127.0.0.1', 6000)
        self.capture_method = capture_method

        self.shutter = gpiozero.OutputDevice(CAMERA_SHUTTER_PIN)
        self.trigger(False)

        self.ready = threading.Event()
        self.skip_system_check = None

    def run(self):
        if self.capture_method == REMOTE_CAPTURE:
            self.remote_mode()
        elif self.capture_method == DIRECT_CAPTURE:
            self.direct_mode()

    def direct_mode(self):
        print("Camera thread started - direct capture mode")
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
            print("Waiting for camera event")
            event_type, event_data = self.camera.wait_for_event(CAMERA_TIMEOUT * 1000)
            print("Event passed")

            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = self.camera.file_get(event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join("imgs/raw", event_data.name)
                cam_file.save(target_path)

                self.capture_filepath = target_path
                self.ready.set()
#                sleep(0.1)
#                self.ready.clear()

        print("Camera thread stopping")

    def remote_mode(self):
        print("Camera thread started - remote capture mode")

        self.capture_filepath = None
        self.ready.clear()

        if self.connect(self.address):
            self.conn_client.send("skip")
            self.skip_system_check = self.conn_client.recv()

            if self.ready.is_set():
                self.conn_client.send("skip-enable")

            self.conn_client.send("close")
            self.conn_client.close()
        else:
            print("Connection failed")

        if self.skip_system_check:
            print("Skipping system check...")
            return

        self.client_get_image()

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

    def client_get_image(self):
        if self.connect(self.address):
            self.conn_client.send("image")
            self.capture_filepath = self.conn_client.recv()

            self.conn_client.send("close")
            self.conn_client.close()
            self.ready.set()


class PowerMonitor():
    def __init__(self, address):
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

    def current(self):
        try:
            return int(self.ina.current())
        except DeviceRangeError:
            raise Exception("INA219 current range error")

    def voltage(self):
        return self.ina.voltage()


class ADS1115():
    def __init__(self):
        self.ads1115 = Adafruit_ADS1x15.ADS1115(address=I2C_ADC_ADDRESS, busnum=I2C_BUS)

    def get(self, channel, gain):
        return self.ads1115.read_adc(channel, gain)

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
        self.enable = gpiozero.OutputDevice(HV_ENABLE_PIN)
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

    # Not currently working
    def current(self, adc_0_before, adc_1_before, adc_0_during, adc_1_during):
        #hv_current = round(self.hv.current(adc_0_before, adc_1_before, adc_0_during, adc_1_during), 3)
        #print(f"adc_0_before:{adc_0_before},adc_1_before:{adc_1_before},adc_0_during:{adc_0_during},adc_1_during:{adc_1_during}")
        #delta_0 = abs(adc_0_before - adc_0_during)
        #delta_1 = abs(adc_1_before - adc_1_during)

        v_drop_0 = (adc_0_during / ADC_BIT_DEPTH) * ADC_MAX_VOLTAGE_1
        v_drop_1 = (adc_1_during / ADC_BIT_DEPTH) * ADC_MAX_VOLTAGE_1
        v_drop = abs(v_drop_0 - v_drop_1)

        filament_current = v_drop / ADC_R_VDROP

        return filament_current

    def voltage(self, voltage_adc):
        converted_voltage = (voltage_adc / ADC_BIT_DEPTH) * ADC_MAX_VOLTAGE_1

        return round(1000 * converted_voltage / (ADC_R2 / (ADC_R1 + ADC_R2)) / 1_000_000, 3)

    def estimate_voltage(self, filament_current):
        return round(5.20593227*10**-7 * 8814.52450668**(filament_current/1000), 3)


class Interpolation():
    def __init__(self, filename):
        try:
            with open(filename,'rb') as file:
                self.lines = file.readlines()
                self.dacs = []
                self.currents = []

            for line in self.lines:
                row = line.decode().split(",")

                current_value = float(row[0])
                dac_value = float(row[1][:-1])

                self.dacs.append(dac_value)
                self.currents.append(current_value)
        except FileNotFoundError:
            pass

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


class ImageObject():
    def __init__(self, img, filament_current, filament_power, mosfet_voltage, hv_current_estimate, hv_voltage):
        self.img = img
        self.filament_current = filament_current
        self.filament_power = filament_power
        self.mosfet_voltage = mosfet_voltage
        self.hv_current_estimate = hv_current_estimate
        self.hv_voltage = hv_voltage


class Photonic():
    def __init__(self, ignore_exceptions=False, disable_led=False, capture_method=DIRECT_CAPTURE):
        # At exit functions
        self.finished = False
        atexit.register(self.finish)
        signal.signal(signal.SIGTERM, self.finish)
        signal.signal(signal.SIGINT, self.finish)

        # Class variables
        self.ignore_exceptions = ignore_exceptions
        self.capture_attempts = 0
        self.disable_led = disable_led
        self.capture_method = capture_method
        self.interpolation = Interpolation(INTERPOLATE_FILEPATH)

        # Kill other Python XRAY processes
        self.manage_python_processes()

        # ADS1115, Filament, HV, LED, interpolate init
        self.filament = Filament()
        self.adc = ADS1115()
        self.hv = HighVoltage()
        self.led = LED()

        # HV PSU powered check
        if self.hv.present.value != 1:
            if not ignore_exceptions: raise Exception("WARNING: HV PSU NOT DETECTED")
            else: print("WARNING: HV PSU NOT DETECTED")

        # Filament power check
        if self.filament.power.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
            if not ignore_exceptions: raise Exception("WARNING: NO POWER TO FILAMENT")
            else: print("WARNING: NO POWER TO FILAMENT")

        # DSLR init
        try:
            self.dslr = Camera(capture_method)
            self.dslr.start()
            sleep(1)
        except Exception as e:
            print("DSLR Error:", e)


    def capture(self, power, duration, filament_power = ADC_MAX):
        self.capture_attempts += 1

        # LED to yellow
        if not self.disable_led: self.led.set(1, 1)

        # Grab filament current before capture
        adc_0_before = self.adc.average(0, 2)
        adc_current_1_before = self.adc.average(1, 2)

        # Wait for filament to heat up
        self.filament.set(True, filament_power)
        sleep(FILAMENT_WAIT_TIME / 1000)

        # Turn HV and camera on
        self.hv.set(power / 100)
        self.dslr.trigger(True)

        # LED to red
        if not self.disable_led: self.led.set(1, 0)

        print("Capture started")

        with open("assets//capture_stats.csv", "w") as f:
            f.write("elasped_time,filament_current,hv_current,hv_voltage,mosfet_voltage,adc_0_before,adc_1_before,adc_0_during,adc_1_during\n")

            start_time = time.time()

            while (start_time + (duration / 1000)) > int(time.time()):
                current_time = time.time()

                # Get filament current
                filament_current = self.filament.power.current()

                # Get hv current
                adc_0_during = self.adc.get(0, 2)
                adc_1_during = self.adc.get(1, 2)
                hv_current = round(self.hv.current(adc_0_before, adc_1_before, adc_0_during, adc_1_during), 3)

                # Get hv voltage
                hv_voltage = self.hv.voltage(self.adc.get(2, 1))

                # MOSFET voltage
                mosfet_voltage = self.filament.mosfet_voltage(self.adc.get(3, 1))

                f.write(f"{(time.time() - start_time) * 1000},{filament_current},{hv_current},{hv_voltage},{mosfet_voltage},{adc_0_before},{adc_1_before},{adc_0_during},{adc_1_during}\n")

                #if (time.time() - start_time) > (duration / 1000): break

        # Turn camera, HV and filament off
        self.dslr.trigger(False)
        self.hv.set(0)
        self.filament.set(False)
        stop_time = time.time()

        capture_settings = f"{power}% {duration}ms {int(filament_current)}mA ~ {filament_power} {mosfet_voltage}V ~ {hv_voltage}kV"
        print(f"Capture finished: " + capture_settings)

        # LED to yellow
        if not self.disable_led: self.led.set(1, 1)

        # Get image from camera
        print("Waiting for camera capture event...")
        self.dslr.ready.wait(timeout=CAMERA_TIMEOUT)

        #if self.capture_method == DIRECT_CAPTURE:
        #    self.dslr.client_get_image()

        if self.dslr.ready.is_set():
            print("Received", self.dslr.capture_filepath)

            self.dslr.listening = False
            self.capture_attempts = 0
            # LED to green
            if not self.disable_led: self.led.set(0, 1, turn_off_period = 10)

            # Add parameters as text at top left of picture
            img = Image.open(self.dslr.capture_filepath)
            image_draw = ImageDraw.Draw(img)
            image_font = ImageFont.truetype("assets/ARIAL.TTF", 36)
            image_draw.text((40, 40), capture_settings, fill=(255, 255, 255), font=image_font)

            self.capture_attempts = 0

            return ImageObject(img, filament_current, filament_power, mosfet_voltage, hv_current_estimate, hv_voltage)

        print("Did not receive capture after timeout period. Retrying...")

        if self.capture_attempts < MAX_CAPTURE_ATTEMPTS: return self.capture(power, duration, filament_power)

        # Reached max capture attempts
        print("Maximum capture attempts reached")
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
                        p.kill()

                    if filename == "camera.py":
                        if self.capture_method == DIRECT_CAPTURE:
                            print("Killing gphoto2 camera script")
                            p.kill()
                        else:
                            camera_script_running = True

        if self.capture_method == REMOTE_CAPTURE and not camera_script_running:
            camera_thread = subprocess.Popen(["python", "/home/boombrush/Photonic/boot/camera.py"])
            sleep(1)

    def system_check(self):
        return_value = True

        sleep(0.1)
        if self.dslr.skip_system_check:
            return True

        # Filament
        print("Checking filament voltage")
        if self.filament.power.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
            print("FAIL: Filament voltage not present")
            return_value = False

        self.filament.set(True)
        sleep(0.5)
        print("Checking filament current")
        filament_current = self.filament.power.current()
        if filament_current < FILAMENT_CURRENT_THRESHOLD:
            print("FAIL: Filament no load")
            self.filament.set(False)
            return_value = False

        self.filament.set(False)

        # HV
        print("Checking HV")
        if self.hv.present.value != 1:
            print("FAIL: HV PSU Not detected")
            return_value = False

        # Camera
        for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
            print(f"Checking camera attempt {attempt}/{MAX_CAPTURE_ATTEMPTS}")

            self.dslr.trigger(True)
            sleep(0.25)
            self.dslr.trigger(False)

            try:
                self.dslr.ready.wait(timeout=CAMERA_TIMEOUT)
                if self.dslr.capture_filepath:
                    print("Recieved", self.dslr.capture_filepath)
                    break
                else:
                    print("FAIL: DSLR Capture")

                if attempt == MAX_CAPTURE_ATTEMPTS:
                    return_value = False
            except AttributeError:
                return_value = False

        if self.capture_method and return_value:
            if self.dslr.connect(self.dslr.address):
                self.dslr.conn_client.send("skip-enable")
                self.dslr.conn_client.send("close")
                self.dslr.conn_client.close()

        print("LED testing")

        self.led.set(1, 0)
        sleep(2)
        self.led.set(1, 1)
        sleep(2)
        self.led.set(0, 1)
        sleep(2)
        self.led.set(0, 0)
        sleep(2)

        self.led.flash(1, 0)
        sleep(5)
        self.led.set(0, 0)
        sleep(5)

        self.led.flash(1, 1)
        sleep(5)
        self.led.set(0, 0)
        sleep(5)

        self.led.flash(0, 1)
        sleep(5)
        self.led.set(0, 0)

        return return_value

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
            self.led.running = False
        except Exception:
            print("Exception in finish method!")

