import threading, gpiozero, os
import gphoto2 as gp
from time import sleep
from PIL import Image, ImageDraw, ImageFont

CAMERA_SHUTTER_PIN = 25
CAMERA_TIMEOUT = 10
IMG_TMP_FILEPATH = "imgs/tmp.cr2"


class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.address = ('127.0.0.1', 6000)

        self.shutter = gpiozero.OutputDevice(CAMERA_SHUTTER_PIN)
        self.trigger(False)

        self.ready = threading.Event()

    def run(self):
        print("Camera thread started")
        self.camera = gp.Camera()
        camera_list = list(gp.Camera.autodetect())

        if len(camera_list) > 0:
            self.camera.init()
            print(camera_list[0][0], "initialized")

            self.detected = True
        else:
            raise Exception("No DSLR camera detected")

        self.capture_filepath = None
        self.listening = True

        while self.listening:
            event_type, event_data = self.camera.wait_for_event(CAMERA_TIMEOUT * 1000)

            if event_type == gp.GP_EVENT_FILE_ADDED:
                print("Recieved image")
                self.image = self.camera.file_get(event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                self.ready.set()

        print("Camera thread stopping")

    def trigger(self, state):
        if state:
            self.shutter.off()
        else:
            self.shutter.on()

    def save(self, filepath, text=""):
        self.image.save(IMG_TMP_FILEPATH)
        img = Image.open(IMG_TMP_FILEPATH)
        image_draw = ImageDraw.Draw(img)
        image_font = ImageFont.truetype("assets/ARIAL.TTF", 36)
        image_draw.text((40, 40), text, fill=(255, 255, 255), font=image_font)
        img.save(filepath)

        os.remove("imgs/tmp.cr2")
        self.ready.clear()

if __name__ == "__main__":
    dslr = Camera()

    dslr.start()

    for i in range(5):
        print("DSLR Capture", i)
        dslr.ready.wait(10)

        if dslr.ready.is_set():
            print("Saving image")
            dslr.save("imgs/dslr.jpg")
        else:
            print("Did not capture")
