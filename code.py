import time
import os
import displayio
from jpegio import JpegDecoder
from adafruit_ticks import ticks_less, ticks_ms, ticks_add, ticks_diff
from adafruit_pycamera import PyCameraBase, PyCamera
from adafruit_bus_device.i2c_device import I2CDevice
import espcamera
import storage
import sdcardio
import board
from digitalio import DigitalInOut, Pull
import adafruit_pycamera
import terminalio
from adafruit_display_text import label

import microcontroller

DISPLAY_INTERVAL = 8000  # milliseconds

decoder = JpegDecoder()
pycam = PyCameraBase()
def load_resized_image(bitmap, filename):
    # print(f"loading {filename}")
    bitmap.fill(0b01000_010000_01000)  # fill with a middle grey

    bw, bh = bitmap.width, bitmap.height
    t0 = ticks_ms()
    h, w = decoder.open(filename)
    t1 = ticks_ms()
    # print(f"{ticks_diff(t1, t0)}ms to open")
    scale = 0
    # print(f"Full image size is {w}x{h}")
    # print(f"Bitmap is {bw}x{bh} pixels")
    while (w >> scale) > bw or (h >> scale) > bh and scale < 3:
        scale += 1
    sw = w >> scale
    sh = h >> scale
    # print(f"will load at {scale=}, giving {sw}x{sh} pixels")

    if sw > bw:  # left/right sides cut off
        x = 0
        x1 = (sw - bw) // 2
    else:  # horizontally centered
        x = (bw - sw) // 2
        x1 = 0
    if sh > bh:  # top/bottom sides cut off
        y = 0
        y1 = (sh - bh) // 2
    else:  # vertically centered
        y = (bh - sh) // 2
        y1 = 0
    # print(f"{x=} {y=} {x1=} {y1=}")
    decoder.decode(bitmap, x=x, y=y, x1=x1, y1=y1, scale=scale)
    t1 = ticks_ms()
    # print(f"{ticks_diff(t1, t0)}ms to decode")

pycam.modes = "JPEG"
pycam.resolutions = (
    # "160x120",
    # "176x144",
    # "240x176",
    "240x240",
    "320x240",
    # "400x296",
    # "480x320",
    "640x480",
    "800x600",
    "1024x768",
    "1280x720",
    "1280x1024",
    "1600x1200",
    "1920x1080",
    # "720x1280",
    # "864x1536",
    "2048x1536",
    "2560x1440",
    "2560x1600",
    # "1080x1920",
    "2560x1920",
)
pycam.effects = "Normal"
pycam.led_levels = [0.0, 0.1, 0.2, 0.5, 1.0]
pycam.make_camera_ui()
pycam.init_accelerometer()
pycam.init_neopixel()
pycam.init_display()
pycam.init_camera()
pycam.mode = 0  # only mode 0 (JPEG) will work in this example

# User settings - try changing these:
pycam.resolution = 8  # 0-12 preset resolutions:
#                      0: 240x240, 1: 320x240, 2: 640x480, 3: 800x600, 4: 1024x768,
#                      5: 1280x720, 6: 1280x1024, 7: 1600x1200, 8: 1920x1080, 9: 2048x1536,
#                      10: 2560x1440, 11: 2560x1600, 12: 2560x1920
pycam.led_level = 0  # 0-4 preset brightness levels
pycam.led_color = 0  # 0-7  preset colors: 0: white, 1: green, 2: yellow, 3: red,
#                                          4: pink, 5: blue, 6: teal, 7: rainbow
pycam.effect = 0  # 0-7 preset FX: 0: normal, 1: invert, 2: b&w, 3: red,
#                                  4: green, 5: blue, 6: sepia, 7: solarize
#pycam.mount_sd_card()

last_frame = displayio.Bitmap(pycam.camera.width, pycam.camera.height, 65535)

def main():
    image_counter = 0
    last_image_counter = 0
    deadline = ticks_ms()
    print("deadline")
    pycam.mount_sd_card()
    bitmap = displayio.Bitmap(pycam.display.width, pycam.display.height, 65535)
    now_counter = 0
    pycam.live_preview_mode()
    pycam.display.refresh()
    while True:
        pycam.blit(pycam.continuous_capture())
        pycam.display.refresh()
        pycam.keys_debounce()
        if pycam.ok.fell:
            pycam.led_level+=1
        if pycam.shutter.long_press:
            print("FOCUS")
            print(pycam.autofocus_status)
            pycam.autofocus()
            pycam.tone(200, 0.05)
            pycam.tone(100, 0.05)
            print(pycam.autofocus_status)
        if pycam.shutter.short_count:
            print("Shutter released")
            pycam.capture_into_bitmap(last_frame)
            #pycam.stop_motion_frame += 1
            try:
                pycam.display_message("Snap!", color=0x0000FF)
                pycam.capture_jpeg()
                pycam.tone(100, 0.05)
                pycam.tone(50, 0.05)
            except TypeError as e:
                pycam.display_message("Failed", color=0xFF0000)
                time.sleep(0.5)
            except RuntimeError as e:
                pycam.display_message("Error\nNo SD Card", color=0xFF0000)
                time.sleep(0.5)
            pycam.live_preview_mode()
        if pycam.select.fell:
            print("select!")
            all_images = [
            f"/sd/{filename}"
            for filename in os.listdir("/sd")
            if filename.lower().endswith(".jpg")
            ]
            image_counter = len(all_images)-1
            while True:
                pycam.keys_debounce()
                if pycam.select.fell:
                    print("back")
                    #pycam.make_camera_ui()
                    pycam.init_display()
                    pycam.display.refresh()
                    pycam.live_preview_mode()
                    break
                if pycam.card_detect.fell:
                    print("SD card removed")
                    pycam.unmount_sd_card()
                    pycam.display_message("SD Card\nRemoved", color=0xFFFFFF)
                    time.sleep(0.5)
                    pycam.display.refresh()
                    all_images = []
                    pycam.display.refresh()
                if pycam.card_detect.rose:
                    print("SD card inserted")
                    pycam.mount_sd_card()
                    all_images = [
                        f"/sd/{filename}"
                        for filename in os.listdir("/sd")
                        if filename.lower().endswith(".jpg")
                        ]
                    image_counter = 0
                    pycam.display.refresh()
                if all_images:
                    if pycam.left.fell:
                        image_counter = (last_image_counter - 1) % len(all_images)
                        # deadline = now
                        print("left")
                    if pycam.right.fell:
                        image_counter = (last_image_counter + 1) % len(all_images)
                        # deadline = now
                        print("right")
                    # print(now, deadline, ticks_less(deadline, now), all_images)
                    # deadline = ticks_add(deadline, DISPLAY_INTERVAL)
                    filename = all_images[image_counter]
                    last_image_counter = image_counter
                    # image_counter = (image_counter) % len(all_images)
                    if now_counter != image_counter:
                        try:
                            load_resized_image(bitmap, filename)
                            now_counter = image_counter
                        except Exception as e:  # pylint: disable=broad-exception-caught
                            pycam.display_message(
                                f"Failed to read\n{filename}", color=0xFF0000
                            )
                            print(e)
                        # deadline = ticks_add(now, 500)
                    pycam.blit(bitmap, y_offset=0)
                    pycam.display.refresh()


main()
