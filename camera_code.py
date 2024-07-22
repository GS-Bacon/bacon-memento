import time

import displayio
import bacon_pycamera
import os

import terminalio
from adafruit_display_text import label
from analogio import AnalogIn
import board
from jpegio import JpegDecoder
decoder = JpegDecoder()

class camera():
    def __init__(self) -> None:
        self.pycam=bacon_pycamera.BaconPyCamera()
        self.pycam.resolution = 8
        self.pycam.led_level = 0
        self.pycam.led_color = 0
        self.last_frame = displayio.Bitmap(self.pycam.camera.width, self.pycam.camera.height, 65535)
        self.splash = displayio.Group()
        self.battery_p:int=0
        self.sd_p:int=0  #def capture_ui(self):
    def preview(self,bitmap):
        print("go preview")
        all_images = [
        f"/sd/{filename}"
        for filename in os.listdir("/sd")
        if filename.lower().endswith(".jpg")
        ]
        image_counter = -1
        last_image_counter = 0
        now_counter=0
        bitmap.fill(0b01000_010000_01000)
        while True:
            self.pycam.keys_debounce()
            if self.pycam.select.fell:
                #bitmap.fill(0b01000_010000_01000)
                #self.pycam.blit(bitmap, y_offset=0)
                self.pycam.live_preview_mode()
                self.pycam.init_display()
                print("back")
                break
            if all_images:
                    if self.pycam.left.fell:
                        image_counter = (last_image_counter - 1) % len(all_images)
                        #deadline = now
                        print("left")
                    if self.pycam.right.fell:
                        image_counter = (last_image_counter + 1) % len(all_images)
                        #deadline = now
                        print("right")
                    if now_counter!=image_counter:
                        #print(now, deadline, ticks_less(deadline, now), all_images)
                        #deadline = ticks_add(deadline, DISPLAY_INTERVAL)
                        filename = all_images[image_counter]
                        last_image_counter = image_counter
                        print(filename)
                        h,w=decoder.open(filename)
                        bw, bh = bitmap.width, bitmap.height
                        scale=1
                        print("a")
                        while (w >> scale) > bw or (h >> scale) > bh and scale < 3:
                            scale += 1
                        sw = w >> scale
                        sh = h >> scale
                        #print(f"will load at {scale=}, giving {sw}x{sh} pixels")
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
                        decoder.decode(bitmap,x=0,y=40,x1=x1,y1=y1,scale=scale)
                        now_counter=image_counter
                    self.pycam.blit(bitmap, y_offset=0)
    
    def main_roop(self):
        last_frame = displayio.Bitmap(self.pycam.camera.width, self.pycam.camera.height, 65535)
        self.pycam.init_display()
        bitmap = displayio.Bitmap(self.pycam.display.width, self.pycam.display.height, 65535)
        sd_label = label.Label(
            terminalio.FONT, text='SD Card {: >3}%'.format(self.sd_p), x=160, y=10, scale=1
            )
        battery_label = label.Label(
            terminalio.FONT, text='Battery {: >3}%'.format(self.battery_p), x=160, y=20, scale=1
            )
        res_label = label.Label(
            terminalio.FONT, text=self.pycam.cam_status.res, x=0, y=10, scale=1
            )
        focus_label = label.Label(
            terminalio.FONT, text="", x=0, y=20, scale=1
            )
        self.pycam.splash.append(sd_label)
        self.pycam.splash.append(battery_label)
        self.pycam.splash.append(res_label)
        print(type(self.pycam.splash))
        pin=self.pycam.batt
        self.battery_p=round((pin.value-500)/41000*100)
        battery_label.text='Battery {: >3}%'.format(self.battery_p)
        batt_counter=0
        while True:
            self.pycam.display.refresh()
            self.pycam.keys_debounce()
            #self.capture_ui()
            self.pycam.blit(self.pycam.continuous_capture())
            #バッテリー残量表示
            if batt_counter%30==0:
                batt_counter=0
                pin=self.pycam.batt
                self.battery_p=round((pin.value-500)/41500*100)
                battery_label.text='Battery {: >3}%'.format(self.battery_p)
            batt_counter=batt_counter+1
            if self.pycam.shutter.long_press:
                print("FOCUS")
                print(self.pycam.autofocus_status)
                self.pycam.autofocus()
                self.pycam.tone(200, 0.05)
                self.pycam.tone(100, 0.05)
                print(self.pycam.autofocus_status)
            if self.pycam.shutter.short_count:
                print("Shutter released")
                self.pycam.capture_into_bitmap(last_frame)
                #pycam.stop_motion_frame += 1
                try:
                    self.pycam.display_message("Snap!", color=0x0000FF)
                    self.pycam.capture_jpeg()
                    self.pycam.tone(100, 0.05)
                    self.pycam.tone(50, 0.05)
                except TypeError as e:
                    self.pycam.display_message("Failed", color=0xFF0000)
                    time.sleep(0.5)
                except RuntimeError as e:
                    self.pycam.display_message("Error\nNo SD Card", color=0xFF0000)
                    time.sleep(0.5)
                self.pycam.live_preview_mode()
            if self.pycam.select.fell:
                self.preview(bitmap)

if __name__=="__main__":
    cameras=camera()
    cameras.main_roop()
