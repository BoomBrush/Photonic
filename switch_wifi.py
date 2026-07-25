import gpiozero, subprocess
from time import sleep, time
from multiprocessing.connection import Client
from LED import LED


def set_led(r, g, b, turn_off_period=0):
    led.connect()
    led.set(r, g, b, turn_off_period)
    led.disconnect()

def on_high():
    print("Connecting to wifi network")
    set_led(1, 0, 0)
    subprocess.run(["sudo", "nmcli", "device", "wifi", "connect", "boombrush", "password", "8%OCEhJVJhq$t@1"])
    set_led(0, 1, 0, turn_off_period = 10)


def on_low():
    print("Creating wifi access point")
    set_led(1, 0, 0)
    subprocess.run(["sudo", "nmcli", "device", "wifi", "hotspot", "ssid", "Photonic Machine", "password", "boombrush", "ifname", "wlan0"])
    set_led(0, 1, 0, turn_off_period = 10)


# Declarations
SWITCH_NETWORKS_PIN = 18
switch = gpiozero.InputDevice(SWITCH_NETWORKS_PIN)
LED_STAY_ON_PERIOD = 10

last_state = None

led = LED()
led.start()

while True:
    current_state = switch.value

    if current_state != last_state:
        if current_state == 0:
            on_low()

        elif current_state == 1:
            on_high()

        last_state = current_state

    sleep(0.25)
