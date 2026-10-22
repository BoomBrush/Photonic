from time import sleep
import Photonic


XRAY = Photonic.Photonic(disable_led=True, remote_capture=True)


filament_power_levels = [3000, 3000, 3000, 3000, 3000]

print(filament_power_levels)

with open("assets/filament_value_to_hv.csv", 'w') as file:
    for power_level in filament_power_levels:
        print(f"XRAY at {power_level} power")
        scan = XRAY.capture(100, 1000, power_level)

        stats = f"{scan.filament_power},{scan.filament_current},{scan.hv_voltage}"
        print(stats)
        file.write(stats + "\n")

        scan.img.save("imgs/multiscan_" + str(power_level) + ".jpg")

XRAY.finish()
