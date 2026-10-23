from time import sleep
import Photonic


if __name__ == "__main__":
    XRAY = Photonic.Photonic(ignore_exceptions=True, capture_method=Photonic.DIRECT_CAPTURE)

    if XRAY.system_check():
        if not XRAY.dslr.skip_system_check:
            print("System check passed")
    else:
        if not XRAY.dslr.skip_system_check:
            print("System check failed")

    XRAY.finish()

