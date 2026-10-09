from time import sleep
from Photonic import *


def system_check(XRAY):
    print("System check started")
    return_value = True

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

    #XRAY.hv(0.5)
    #sleep(0.25)

    #vout = XRAY.hv_highside.voltage()
    #if vout < 1.0:
    #    print("FAIL: HV Not present")
   #     return_value = False

    #high_voltage = XRAY.calculate_hv(vout)
    #if high_voltage < HV_VOLTAGE_THRESHOLD:
    #    print("FAIL: HV below threshold")
    #    return_value = False

    #XRAY.hv(0)

    # Camera
    if not XRAY.dslr.skip_system_check:
        for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
            print(f"Checking camera attempt {attempt}/{MAX_CAPTURE_ATTEMPTS}")

            XRAY.dslr.trigger(True)
            sleep(0.25)
            XRAY.dslr.trigger(False)

            try:
                XRAY.dslr.ready.wait(timeout=CAMERA_TIMEOUT)

                if XRAY.dslr.capture_filepath:
                    print("Recieved test image from camera")
                    break
                else:
                    print("FAIL: DSLR Capture")

                if attempt == MAX_CAPTURE_ATTEMPTS:
                    return_value = False
            except AttributeError:
                return_value = False

    return return_value

if __name__ == "__main__":
    XRAY = Photonic(ignore_exceptions=True, disable_led=True)

    if system_check(XRAY):
        print("System check passed!")
    else:
        print("System check failed")

    XRAY.finish()

