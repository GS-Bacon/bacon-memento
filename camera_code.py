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
import bitmaptools
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
        self.led_level:int=0
        self.last_frame=None
        self.sd_label=None
        self.battery_label=None
        self.res_label=None
        self.focus_label=None
        self.file_name=None
        self.led_label=None

    def preview(self,bitmap):
        self.file_name.text=f''
        print("go preview")
        all_images = [
        f"/sd/{filename}"
        for filename in os.listdir("/sd")
        if filename.lower().endswith(".jpg")
        ]
        image_counter = -1
        last_image_counter = 0
        now_counter=0
        #bitmap.fill(0b01000_010000_01000)
        while True:
            self.pycam.keys_debounce()
            if self.pycam.select.fell:
                self.pycam.live_preview_mode()
                self.pycam.init_display()
                print("back")
                break
            if all_images:
                if self.pycam.left.fell:
                    image_counter = (last_image_counter - 1) % len(all_images)
                    bitmap.fill(0b01000_010000_01000)
                    #deadline = now
                    print("left")
                if self.pycam.right.fell:
                    image_counter = (last_image_counter + 1) % len(all_images)
                    bitmap.fill(0b01000_010000_01000)
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
                    #bitmaptools.rotozoom(bitmap,bitmap,scale=1.2)
                self.pycam.blit(bitmap, y_offset=0)
                self.pycam.display.root_group = self.splash
    
    def init(self):
        self.last_frame = displayio.Bitmap(self.pycam.camera.width, self.pycam.camera.height, 65535)
        self.sd_label = label.Label(
            terminalio.FONT, text='SD Card {: >3}%'.format(self.sd_p), x=160, y=10, scale=1
            )
        self.battery_label = label.Label(
            terminalio.FONT, text='Battery {: >3}%'.format(self.battery_p), x=160, y=20, scale=1
            )
        self.res_label = label.Label(
            terminalio.FONT, text=self.pycam.cam_status.res, x=0, y=10, scale=1
            )
        self.focus_label = label.Label(
            terminalio.FONT, text="", x=0, y=20, scale=1
            )
        self.file_name=label.Label(
            terminalio.FONT, text=f'', x=140, y=220, scale=1
            )
        self.led_label=label.Label(
            terminalio.FONT, text=f'LED {self.pycam.led_level}', x=10, y=220, scale=1
            )
        self.gain_label=label.Label(
            terminalio.FONT, text=f'Gain {self.pycam.camera_gain}', x=140, y=220, scale=1
            )
        self.pycam.splash.append(self.sd_label)
        self.pycam.splash.append(self.battery_label)
        self.pycam.splash.append(self.res_label)
        self.pycam.splash.append(self.file_name)
        self.pycam.splash.append(self.led_label)
        self.pycam.splash.append(self.gain_label)
    def main_roop(self):
        self.init()
        self.pycam.init_display()
        batt_test=0
        batt_test_counter=0
        bitmap = displayio.Bitmap(self.pycam.display.width, self.pycam.display.height, 65535)
        path="/sd/battery2.csv"
        pin=self.pycam.batt
        self.battery_p=round((pin.value-500)/41000*100)
        self.battery_label.text='Battery {: >3}%'.format(self.battery_p)
        batt_counter=0
        batt_sum:float=0.0
        while True:
            if self.pycam.camera_gain==0:
                self.gain_label.text="Gain Auto"
            else:
                self.gain_label.text=f'Gain {self.pycam.camera_gain}'
            self.pycam.display.refresh()
            #print(f'aec:{self.pycam.camera.aec_value}')
            self.pycam.keys_debounce()
            #self.capture_ui()
            self.pycam.blit(self.pycam.continuous_capture())
            self.led_label.text=f'LED {self.pycam.led_level}'
            #バッテリー残量表示
            if batt_counter%60==0:
                batt_counter=0
                pin=self.pycam.batt
                self.battery_p=round(batt_sum/60.0)
                self.battery_label.text='Battery {: >3}%'.format(self.battery_p)
                batt_sum=0
                print(self.battery_label.text)
                s=f'{time.time()},{pin.value}\n'
                if not self.battery_p==100:
                    with open(path,mode='a')as f:
                        print(s)
                        f.write(s)
            
            batt_sum+=round(abs(41000-round(pin.value))/9000*100)
            batt_counter=batt_counter+1
            if self.pycam.shutter.long_press:
                print("FOCUS")
                print(self.pycam.autofocus_status)
                self.pycam.autofocus()
                self.pycam.tone(90, 0.05)
                self.pycam.tone(60, 0.05)
                print(self.pycam.autofocus_status)
            if self.pycam.shutter.short_count:
                print("Shutter released")
                self.pycam.capture_into_bitmap(self.last_frame)
                #pycam.stop_motion_frame += 1
                try:
                    self.pycam.display_message("Snap!", color=0x0000FF)
                    if self.pycam.capture_jpeg():
                        self.pycam.tone(60, 0.05)
                        self.pycam.tone(30, 0.05)
                    else:
                        self.pycam.display_message("failed...", color=0x0000FF)
                        #self.pycam.tone(50, 0.05)
                        #self.pycam.tone(100, 0.05)
                except TypeError as e:
                    self.pycam.display_message("Failed", color=0xFF0000)
                    time.sleep(0.5)
                except RuntimeError as e:
                    self.pycam.display_message("Error\nNo SD Card", color=0xFF0000)
                    time.sleep(0.5)
                self.pycam.live_preview_mode()
            if self.pycam.select.fell:
                self.preview(bitmap)
                self.pycam.live_preview_mode()
            if self.pycam.ok.fell:
                self.pycam.led_level+=1
            if self.pycam.up.fell:
                self.pycam.camera_gain+=1
            if self.pycam.down.fell:
                self.pycam.camera_gain-=1
if __name__=="__main__":
    cameras=camera()
    cameras.main_roop()
