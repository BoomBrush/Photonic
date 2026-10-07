
class FilamentInterpolation():
    def __init__(self, filename):
        with open(filename,'rb') as file:
            self.lines = file.readlines()
            self.dacs = []
            self.currents = []

        for line in self.lines:
            row = line.decode().split(",")

            dac_value = int(row[0])
            current_value = float(row[1][:-1])

            #print(f"DAC:{dac_value}, Current:{current_value}")

            self.dacs.append(dac_value)
            self.currents.append(current_value)

    def current_from_dac(self, current_value):
        return 2.03394873*10**-09 * 1.00980772**current_value

    def dac_from_current(self, dac_value):
        

if __name__ == "__main__":
    filament_interpolation = FilamentInterpolation("assets//filament_currents.csv")
    filament_interpolation.desired_dac_value(2500)


