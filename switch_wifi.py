import gpiozero, subprocess
from time import sleep
from Photonic import SWITCH_NETWORKS_PIN

switch = gpiozero.InputDevice(SWITCH_NETWORKS_PIN)

def on_high():
    print("Connecting to wifi network")
    subprocess.run(["sudo", "nmcli", "device", "wifi", "connect", "boombrush", "password", "8%OCEhJVJhq$t@1"])

def on_low():
    print("Creating wifi access point")
    subprocess.run(["sudo", "nmcli", "device", "wifi", "hotspot", "ssid", "Photonic Machine", "password", "boombrush", "ifname", "wlan0"])

last_state = None

while True:
    current_state = switch.value

    if current_state != last_state:
        if current_state == 0:
            on_low()
        elif current_state == 1:
            on_high()

        last_state = current_state

    sleep(0.5)
