from time import sleep
from Photonic import *


def system_check(XRAY):
    return_value = True

    sleep(0.1)
    if XRAY.dslr.skip_system_check:
        return True

    # Filament
    print("Checking filament voltage")
    if XRAY.filament.power.voltage() < FILAMENT_VOLTAGE_THRESHOLD:
        print("FAIL: Filament voltage not present")
        return_value = False

    XRAY.filament.set(True)
    sleep(0.5)
    print("Checking filament current")
    if XRAY.filament.power.current() < FILAMENT_CURRENT_THRESHOLD:
        print("FAIL: Filament no load")
        XRAY.filament.set(False)
        return_value = False

    XRAY.filament.set(False)

    # HV
    print("Checking HV")
    if XRAY.hv.present.value != 1:
        print("FAIL: HV PSU Not detected")
        return_value = False

    # Camera
    for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
        print(f"Checking camera attempt {attempt}/{MAX_CAPTURE_ATTEMPTS}")

        XRAY.dslr.trigger(True)
        sleep(0.25)
        XRAY.dslr.trigger(False)

        try:
            XRAY.dslr.ready.wait(timeout=CAMERA_TIMEOUT)
            if XRAY.dslr.capture_filepath:
                print("Recieved", XRAY.dslr.capture_filepath)
                break
            else:
                print("FAIL: DSLR Capture")

            if attempt == MAX_CAPTURE_ATTEMPTS:
                return_value = False
        except AttributeError:
            return_value = False

    if XRAY.remote_capture and return_value:
        if XRAY.dslr.connect(XRAY.dslr.address):
            XRAY.dslr.conn_client.send("skip-enable")
            XRAY.dslr.conn_client.send("close")
            XRAY.dslr.conn_client.close()

    return return_value


if __name__ == "__main__":
    XRAY = Photonic(disable_led=True, ignore_exceptions=True, remote_capture=True)

    if system_check(XRAY):
        if not XRAY.dslr.skip_system_check:
            print("System check passed")
    else:
        if not XRAY.dslr.skip_system_check:
            print("System check failed")

    XRAY.finish()

