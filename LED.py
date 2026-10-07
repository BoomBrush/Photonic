from multiprocessing.connection import Listener, Client
import gpiozero, threading
from time import time, sleep


# Definitions
LED_RED_PIN = 20
LED_GREEN_PIN = 16


class LED(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self.led_r = gpiozero.PWMOutputDevice(LED_RED_PIN)
        self.led_g = gpiozero.OutputDevice(LED_GREEN_PIN)

        address = ('127.0.0.1', 5000)     # family is deduced to be 'AF_INET'

        while True:
            listener = Listener(address, authkey=b'boombrush')
            self.conn = listener.accept()
            print('connection accepted from', listener.last_accepted)

            while True:
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
                elif msg.split(",")[0] == "msg":
                    print("server recieved:", msg)
                    sleep(5)
                    self.conn.send(msg[1])
                    print("server sent msg back")

            listener.close()

    def set(self, r, g, turn_off_period=0):
        self.connect()

        if turn_off_period == 0:
            self.conn_client.send([r, g])
        else:
            self.conn_client.send([r, g, turn_off_period])

        self.disconnect()

    def connect(self):
        address = ('127.0.0.1', 5000)
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

    sleep(1)

    led.connect()

    led.conn_client.send("msg,abc")
    print("Sent message")
    #recieved = led.conn_client.recv()
    #print("Recieved message")
    #print(recieved)
    sleep(1)
    print("post sleep")
    msg = led.conn.recv()
    print("client recieved:", msg)

    led.disconnect()


    '''
    while True:
        led.set(1, 0)
        sleep(1)
        led.set(1, 1)
        sleep(1)
        led.set(0, 1)
        sleep(1)
    '''
