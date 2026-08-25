import gpiozero, subprocess, os, sys, socket
from time import sleep, time
from multiprocessing.connection import Client

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from LED import LED


# Declarations
SWITCH_NETWORKS_PIN = 6
LED_STAY_ON_PERIOD = 10


def get_ip():
    gw = os.popen("ip -4 route show default").read().split()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((gw[2], 0))
    return s.getsockname()[0]

def set_led(r, g, b, turn_off_period=0):
    led.connect()
    led.set(r, g, b, turn_off_period)
    led.disconnect()

def connect_to_wifi():
    print("Connecting to wifi network")
    set_led(1, 0, 0)
    subprocess.run(["sudo", "nmcli", "device", "wifi", "connect", "boombrush", "password", "8%OCEhJVJhq$t@1"])
    set_led(0, 1, 0, turn_off_period = LED_STAY_ON_PERIOD)

def create_access_point():
    print("Creating wifi access point")
    set_led(1, 0, 0)
    subprocess.run(["sudo", "nmcli", "device", "wifi", "hotspot", "ssid", "Photonic Machine", "password", "boombrush", "ifname", "wlan0"])
    set_led(0, 1, 0, turn_off_period = LED_STAY_ON_PERIOD)


switch = gpiozero.InputDevice(SWITCH_NETWORKS_PIN)
led = LED()
led.start()

last_state = None

while True:
    current_state = switch.value

    if current_state != last_state:
        if current_state == 0:
            create_access_point()

        elif current_state == 1:
            connect_to_wifi()

        last_state = current_state

    sleep(0.25)
