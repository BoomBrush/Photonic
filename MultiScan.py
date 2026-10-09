from time import sleep
import Photonic
import SystemCheck


XRAY = Photonic.Photonic()


filament_power_levels = list(range(2000, 4095, 100))
print(filament_power_levels)


for power_level in filament_power_levels:
    print(f"XRAY at {power_level} power")
    img = XRAY.capture(100, 3000, power_level)
    img.save(f"imgs/multiscan_{power_level}.jpg")

XRAY.finish()
