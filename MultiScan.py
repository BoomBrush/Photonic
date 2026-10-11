from time import sleep
import Photonic
import SystemCheck


XRAY = Photonic.Photonic(disable_led=True, remote_capture=True)


filament_power_levels = list(range(2700, 2730, 5))
print(filament_power_levels)

with open("assets/filament_value_to_hv.csv", 'w') as file:
    for power_level in filament_power_levels:
        print(f"XRAY at {power_level} power")
        img, filament_current, hv = XRAY.capture(100, 3000, power_level)

        file.write(f"{power_level},{filament_current},{hv}\n")

XRAY.finish()
