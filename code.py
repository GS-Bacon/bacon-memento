
import displayioimport bacon_pycamera
pycam=bacon_pycamera.BaconPyCamera()

pycam.resolution = 8

pycam.led_level = 0
pycam.led_color = 0

last_frame = displayio.Bitmap(pycam.camera.width, pycam.camera.height, 65535)