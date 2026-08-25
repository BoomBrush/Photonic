from time import sleep
from Photonic import *


def system_check(XRAY):
    print("System check started")
    return_value = True

    # Filament
    print("Checking filament")
    if XRAY.filament_psu.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
        print("FAIL: Filament voltage not present")
        return_value = False

    XRAY.filament(True)
    sleep(0.5)
    if XRAY.filament_psu.power() < FILAMENT_POWER_THRESHOLD:
        print("FAIL: Filament no load")
        XRAY.filament(False)
        return_value = False

    XRAY.filament(False)

    # HV
    print("Checking HV")
    if XRAY.gpio_hv_power.value != 1:
        print("FAIL: HV PSU Not detected")
        return_value = False

    XRAY.hv(0.5)
    sleep(0.25)

    vout = XRAY.hv_highside.voltage()
    if vout < 1.0:
        print("FAIL: HV Not present")
        return_value = False

    high_voltage = XRAY.calculate_hv(vout)
    if high_voltage < HV_VOLTAGE_THRESHOLD:
        print("FAIL: HV below threshold")
        return_value = False

    XRAY.hv(0)

    # Camera
    for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
        print(f"Checking camera attempt {attempt}/{MAX_CAPTURE_ATTEMPTS}")

        XRAY.camera_shutter(True)
        sleep(0.25)
        XRAY.camera_shutter(False)

        if not XRAY.ignore_camera:
            XRAY.dslr.capture_successful.wait(timeout=CAMERA_TIMEOUT)

            if XRAY.dslr.capture_filepath:
                print("Recieved image from camera")
                break
            else:
                print("FAIL: DSLR Capture")

        if attempt == MAX_CAPTURE_ATTEMPTS:
            return_value = False

    return return_value


if __name__ == "__main__":
    XRAY = Photonic()

    if system_check(XRAY):
        print("System check passed!")
    else:
        print("System check failed")

    XRAY.finished()
