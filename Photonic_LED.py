from multiprocessing.connection import Listener
from Photonic import Photonic

XRAY = Photonic(skip_initializations = True)

address = ('127.0.0.1', 6000)
listener = Listener(address, authkey=b'boombrush')
conn = listener.accept()

print('connection accepted from', listener.last_accepted)

while True:
    msg = conn.recv()

    if len(msg) == 3 and type(msg) == list:
        XRAY.led(msg[0], msg[1], msg[2])

    if msg == 'close':
        conn.close()
        break

listener.close()
