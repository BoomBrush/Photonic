from multiprocessing.connection import Listener, Client
import gpiozero, threading
from time import sleep


# Definitions
LED_RED_PIN = 20
LED_GREEN_PIN = 21
LED_BLUE_PIN = 16

class LED(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.blink_event = threading.Event()

    def run(self):
        self.led_r = gpiozero.OutputDevice(LED_RED_PIN)
        self.led_g = gpiozero.OutputDevice(LED_GREEN_PIN)
        self.led_b = gpiozero.OutputDevice(LED_BLUE_PIN)

        address = ('localhost', 6000)     # family is deduced to be 'AF_INET'

        while True:
            listener = Listener(address)
            conn = listener.accept()
            print('connection accepted from', listener.last_accepted)

            while True:
                msg = conn.recv()

                if len(msg) == 3:
                    self.led(msg[0], msg[1], msg[2])
                elif len(msg) == 4:
                    self.led(msg[0], msg[1], msg[2])
                    sleep(msg[3])
                    self.led(0, 0, 0)
                elif msg == 'close':
                    conn.close()
                    break

            listener.close()

    def set(self, r, g, b, turn_off_period=None):
        if turn_off_period:
            self.conn_client.send([r, g, b, turn_off_period])
        else:
            self.conn_client.send([r, g, b])

    def blink(self, r, g, b):
        self.blink_event.set()
        self.set(r, g, b)

    def connect(self):
        address = ('localhost', 6000)
        self.conn_client = Client(address)

    def disconnect(self):
        self.conn_client.send('close')
        self.conn_client.close()

    def led(self, r, g, b):
        if r:
            self.led_r.on()
        else:
            self.led_r.off()

        if g:
            self.led_g.on()
        else:
            self.led_g.off()

        if b:
            self.led_b.on()
        else:
            self.led_b.off()


if __name__ == "__main__":
    led = LED()

    led.connect()
    led.set(0, 0, 0)
    led.disconnect()


