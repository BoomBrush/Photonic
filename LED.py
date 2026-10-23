from multiprocessing.connection import Listener, Client
import gpiozero, threading
from time import time, sleep


# Definitions
LED_RED_PIN = 20
LED_GREEN_PIN = 16


class Flashing(threading.Thread):
    def __init__(self, led, r, g, delay=0.5):
        threading.Thread.__init__(self)
        self.led = led
        self.r = r
        self.g = g
        self.delay = delay

    def run(self):
        self.led.blinking = True

        while self.led.blinking:
            self.led.set(self.r, self.g, flash=True)
            sleep(self.delay)
            self.led.set(0, 0, flash=True)
            sleep(self.delay)


class LED(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.blinking = False
        self.running = True

    def run(self):
        self.led_r = gpiozero.PWMOutputDevice(LED_RED_PIN)
        self.led_g = gpiozero.OutputDevice(LED_GREEN_PIN)

        address = ('127.0.0.1', 4000)     # family is deduced to be 'AF_INET'

        while self.running:
            listener = Listener(address, authkey=b'boombrush')
            self.conn = listener.accept()

            while self.running:
                msg = self.conn.recv()
                if len(msg) == 2:
                    self.led(msg[0], msg[1])
                elif len(msg) == 3:
                    self.led(msg[0], msg[1])
                    sleep(msg[2])
                    self.led(0, 0)
                elif msg == 'close':
                    self.conn.close()
                    break

            listener.close()

        print("LED thread closing")

    def set(self, r, g, turn_off_period=0, flash=False):
        self.connect()

        #if not flash: self.conn_client.send([False])

        if turn_off_period == 0:
            self.conn_client.send([r, g])
        else:
            self.conn_client.send([r, g, turn_off_period])

        self.disconnect()

    def flash(self, r, g, delay=0.1):
        self.connect()
        self.blinking = True

        self.flash_object = Flashing(self, r, g, delay)
        self.flash_object.start()

        self.disconnect()

    def connect(self):
        sleep(0.1)

        address = ('127.0.0.1', 4000)
        try:
            self.conn_client = Client(address, authkey=b'boombrush')
        except Exception as e:
            print("Could not reconnect to LED:", e)

    def disconnect(self):
        self.conn_client.send('close')
        self.conn_client.close()

    def led(self, r, g):
        if r:
            self.led_r.value = 0.5
        else:
            self.led_r.value = 0.0

        if g:
            self.led_g.on()
        else:
            self.led_g.off()


if __name__ == "__main__":
    led = LED()
    led.start()

#    led.set(1, 0)
#    sleep(2)
#    led.set(1, 1)
#    sleep(2)
#    led.set(0, 1)
#    sleep(2)

    led.flash(1, 0)
    sleep(5)
    led.set(0, 0)
    sleep(5)

#    led.flash(0, 1)
#    sleep(5)
#    led.set(0, 0)
#    sleep(5)

#    led.flash(1, 1)
#    sleep(5)
#    led.set(0, 0)
#    sleep(5)
