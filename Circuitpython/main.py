import os
import time

import bacon_pycamera
import displayio
import espcamera
import qrio
import terminalio
from adafruit_display_text import label
from jpegio import JpegDecoder

decoder = JpegDecoder()
bitmap = displayio.Bitmap(240, 176, 65535)


class camera:
    def __init__(self) -> None:
        self.pycam = bacon_pycamera.BaconPyCamera()
        self.pycam.resolution = 8
        self.pycam.led_level = 0
        self.pycam.led_color = 0
        self.last_frame = displayio.Bitmap(
            self.pycam.camera.width, self.pycam.camera.height, 65535
        )
        self.splash = displayio.Group()
        self.battery_p: int = 0
        self.sd_p: int = 0  # def capture_ui(self):
        self.led_level: int = 0
        self.last_frame = None
        self.sd_label = None
        self.battery_label = None
        self.res_label = None
        self.focus_label = None
        self.file_name = None
        self.led_label = None
        self.loop_counter = 0
        self.batt_sum: float = 0.0
        self.ok_flag: bool = False
        self.select_flag: bool = False

    def read_qr(self):
        print("QR MODE")
        qrdecoder = qrio.QRDecoder(self.pycam.camera.width, self.pycam.camera.height)
        while True:
            bitmaps = self.pycam.continuous_capture()
            self.pycam.blit(bitmaps)
            self.pycam.keys_debounce()
            self.batt_check()
            if self.pycam.shutter.long_press:
                print("FOCUS")
                print(self.pycam.autofocus_status)
                self.pycam.autofocus()
            if self.pycam.ok.fell:
                self.pycam.camera.special_effect = 0
                return
            for row in qrdecoder.decode(bitmaps, qrio.PixelPolicy.EVEN_BYTES):
                payload = row.payload
                try:
                    payload = payload.decode("utf-8")
                    print(payload)
                    self.pycam.display_message(f"{payload}", scale=1, color=0x0000FF)
                    return
                except UnicodeError:
                    pass

    def preview(self, bitmap):
        # self.pycam.display.refresh()
        print("go preview")
        all_images = [
            f"/sd/{filename}"
            for filename in os.listdir("/sd")
            if filename.lower().endswith(".jpg")
        ]
        all_images.sort()
        image_counter = -1
        last_image_counter = 0
        now_counter = 0
        self.led_label.text = ""
        self.gain_label.text = ""
        filename = ""
        while True:
            self.pycam.keys_debounce()
            self.batt_check()
            self.file_name.text = filename.split("/")[-1].split(".")[0]
            if self.pycam.select.fell:
                self.pycam.live_preview_mode()
                self.pycam.init_display()
                print("back")
                break
            if all_images:
                if self.pycam.left.fell:
                    image_counter = (last_image_counter - 1) % len(all_images)
                    # bitmap.fill(0)
                    # deadline = now
                    print("left")
                if self.pycam.right.fell:
                    image_counter = (last_image_counter + 1) % len(all_images)
                    # bitmap.fill(0)
                    # deadline = now
                    print("right")
                if now_counter != image_counter:
                    # bitmap.fill(0)
                    # print(now, deadline, ticks_less(deadline, now), all_images)
                    # deadline = ticks_add(deadline, DISPLAY_INTERVAL)
                    filename = all_images[image_counter]
                    last_image_counter = image_counter
                    print(filename)
                    h, w = decoder.open(filename)
                    print(f"load image {h}x{w}")
                    decoder.decode(bitmap, x=0, y=20, x1=0, y1=0, scale=3)
                    print(f"bitmap size")
                    now_counter = image_counter
                    self.pycam.display.refresh()
                    self.file_name.text = filename.split("/")[-1].split(".")[0]
                    self.res_label.text = f"{h}x{w}"
                    # bitmaptools.rotozoom(bitmap,bitmap,scale=1.2)
                self.pycam.blit(bitmap)
                if self.pycam.ok.fell:
                    print("remove check")
                    self.file_name.text = ""
                    del_label = label.Label(
                        terminalio.FONT,
                        text=f"{filename.split('/')[-1].split('.')[0]} remove?",
                        x=0,
                        y=120,
                        scale=2,
                    )
                    ok_label = label.Label(
                        terminalio.FONT, text=f"OK", x=10, y=220, scale=2
                    )
                    cancel_label = label.Label(
                        terminalio.FONT, text=f"Cancel", x=160, y=220, scale=2
                    )
                    self.pycam.splash.append(del_label)
                    self.pycam.splash.append(ok_label)
                    self.pycam.splash.append(cancel_label)
                    self.pycam.display.refresh()
                    while True:
                        self.pycam.keys_debounce()
                        if self.pycam.ok.fell:
                            os.remove(filename)
                            self.pycam.splash[-1].text = "removed!!"
                            self.pycam.display.refresh()
                            self.pycam.splash.pop()
                            self.pycam.splash.pop()
                            self.pycam.splash.pop()
                            all_images = [
                                f"/sd/{filename}"
                                for filename in os.listdir("/sd")
                                if filename.lower().endswith(".jpg")
                            ]
                            all_images.sort()
                            image_counter -= 1
                            break
                        if self.pycam.select.fell:
                            break
                    del_label.text = ""
                    ok_label.text = ""
                    cancel_label.text = ""
        self.file_name.text = f""

    def init_UI(self):
        self.last_frame = displayio.Bitmap(
            self.pycam.camera.width, self.pycam.camera.height, 65535
        )
        self.sd_label = label.Label(
            terminalio.FONT,
            text="SD Card {: >3}%".format(self.sd_p),
            x=160,
            y=10,
            scale=1,
        )
        self.battery_label = label.Label(
            terminalio.FONT,
            text="Battery {: >3}%".format(self.battery_p),
            x=160,
            y=20,
            scale=1,
        )
        self.res_label = label.Label(
            terminalio.FONT, text=self.pycam.cam_status.res, x=0, y=10, scale=1
        )
        self.focus_label = label.Label(terminalio.FONT, text="", x=0, y=20, scale=1)
        self.file_name = label.Label(terminalio.FONT, text=f"", x=10, y=220, scale=2)
        self.led_label = label.Label(
            terminalio.FONT, text=f"LED {self.pycam.led_level}", x=10, y=220, scale=1
        )
        self.gain_label = label.Label(
            terminalio.FONT,
            text="Gain {: >4}".format(self.pycam.camera_gain),
            x=180,
            y=220,
            scale=1,
        )
        self.pycam.splash.append(self.sd_label)
        self.pycam.splash.append(self.battery_label)
        self.pycam.splash.append(self.res_label)
        self.pycam.splash.append(self.file_name)
        self.pycam.splash.append(self.led_label)
        self.pycam.splash.append(self.gain_label)

    def batt_check(self):
        self.loop_counter = self.loop_counter + 1
        pin = self.pycam.batt
        if self.loop_counter % 60 == 0:
            self.battery_p = round(self.batt_sum / 60.0)
            self.battery_label.text = "Battery {: >3}%".format(self.battery_p)
            self.batt_sum = 0
            print(self.battery_label.text)
        self.batt_sum += 100 - round(abs(41000 - round(pin.value)) / 9000 * 100)
        self.pycam.display.refresh()
        # self.set_main_UI()

    def set_main_UI(self):
        if self.pycam.camera_gain == 0:
            self.gain_label.text = "Gain Auto"
        else:
            self.gain_label.text = "Gain {: >4}".format(self.pycam.camera_gain)
        self.pycam.display.refresh()
        self.led_label.text = f"LED {self.pycam.led_level}"
        self.sd_label.text = "SD Card {: >3}%".format(self.sd_p)
        self.res_label.text = self.pycam.cam_status.res
        if self.pycam.camera_gain == 0:
            self.gain_label.text = "Gain Auto"
        else:
            self.gain_label.text = "Gain {: >4}".format(self.pycam.camera_gain)

    def main_roop(self):
        self.init_UI()
        self.set_main_UI()
        self.pycam.init_display()
        self.pycam.camera.gain_ctrl = True
        self.pycam.camera.exposure_ctrl = False
        self.pycam.camera.agc_gain = 0
        self.pycam.camera.aec_value = 830
        self.pycam.camera.brightness = 0
        self.pycam.camera.bpc = False
        self.pycam.camera.denoise = 6
        self.pycam.camera.quality = 6
        self.pycam.camera.bpc = False
        self.pycam.camera.wpc = False
        self.pycam.camera.gain_ceiling = espcamera.GainCeiling.GAIN_2X
        pin = self.pycam.batt
        self.battery_p = 100 - round(abs(41000 - round(pin.value)) / 9000 * 100)
        self.battery_label.text = "Battery {: >3}%".format(self.battery_p)
        while True:
            self.pycam.keys_debounce()
            self.batt_check()
            self.pycam.blit(self.pycam.continuous_capture())
            # print(f'{self.pycam.camera.gain_ctrl=}\n{self.pycam.camera.agc_gain=}\n{self.pycam.camera.aec_value=}')
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
                # pycam.stop_motion_frame += 1
                try:
                    self.pycam.display_message("Snap!", color=0x0000FF)
                    if self.pycam.capture_jpeg():
                        self.pycam.tone(60, 0.05)
                        self.pycam.tone(30, 0.05)
                    else:
                        self.pycam.display_message("failed...", color=0x0000FF)
                        # self.pycam.tone(50, 0.05)
                        # self.pycam.tone(100, 0.05)
                except TypeError as e:
                    self.pycam.display_message("Failed", color=0xFF0000)
                    time.sleep(0.5)
                except RuntimeError as e:
                    self.pycam.display_message("Error\nNo SD Card", color=0xFF0000)
                    time.sleep(0.5)
                self.pycam.live_preview_mode()
            if self.pycam.select.rose:
                self.select_flag = False
            if self.pycam.select.current_duration > 1 and self.select_flag:
                print("select long press")
                pass
                # self.read_qr()
                # self.pycam.live_preview_mode()
            if self.pycam.select.fell and self.pycam.select.last_duration<=1:
                print(f'{self.pycam.select.last_duration=}')
                self.select_flag = True
                self.preview(bitmap)
                self.pycam.display.refresh()
                self.set_main_UI()
                self.pycam.live_preview_mode()
            if self.pycam.ok.fell:
                self.pycam.led_level += 1
                self.ok_flag = True
                print(f"{self.pycam.led_level=}")
                self.pycam.display.refresh()
                self.set_main_UI()
            if self.pycam.ok.rose:
                self.ok_flag = False
            if self.pycam.ok.current_duration > 1 and self.ok_flag:
                print(f"{self.pycam.ok.current_duration=}")
                self.pycam.led_level = 0
                self.pycam.display.refresh()
                self.set_main_UI()
            if self.pycam.up.fell:
                self.pycam.camera_gain += 1
                print(self.pycam.camera_gain)
                self.pycam.display.refresh()
                self.set_main_UI()
            if self.pycam.down.fell:
                self.pycam.camera_gain -= 1
                print(self.pycam.camera_gain)
                self.pycam.display.refresh()
                self.set_main_UI()
            if self.pycam.left.fell:
                self.pycam.live_preview_mode()


if __name__ == "__main__":
    cameras = camera()
    cameras.main_roop()
