from multiprocessing.connection import Client
from time import sleep
from LED import LED

while True:
    LED.set(None, 1, 0, 0)
    sleep(1)
    LED.set(None, 0, 1, 0)
    sleep(1)
    LED.set(None, 0, 0, 1)
    sleep(1)

conn.send('close')
conn.close()
