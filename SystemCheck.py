from time import sleep
import Photonic


if __name__ == "__main__":
    XRAY = Photonic.Photonic(disable_led=True, ignore_exceptions=True)

    if XRAY.system_check():
        print("System check passed")
    else:
        print("System check failed")

    XRAY.finish()

