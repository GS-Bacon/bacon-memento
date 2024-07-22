import time

import displayio
import bacon_pycamera

import terminalio
from adafruit_display_text import label

pycam=bacon_pycamera.BaconPyCamera()

pycam.resolution = 8

pycam.led_level = 0
pycam.led_color = 0

last_frame = displayio.Bitmap(pycam.camera.width, pycam.camera.height, 65535)
splash = displayio.Group()
sd_label = label.Label(
            terminalio.FONT, text="SD ??", x=170, y=10, scale=2
        )
res_label = label.Label(
            terminalio.FONT, text="aaaa", x=0, y=10, scale=2
        )
pycam.splash.append(sd_label)
pycam.splash.append(res_label)
pycam.init_display()
while True:
    #pycam.init_display()
    pycam.display.refresh()
    time.sleep(0.5)