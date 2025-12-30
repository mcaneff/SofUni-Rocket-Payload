import time
import board
import busio

from datetime import datetime
from picamera2.encoders import H264Encoder, Quality
from picamera2 import Picamera2, MappedArray
from gpiozero import LED
import os
from pathlib import Path
import cv2
from libcamera import Transform
from functools import partial

colour = (0, 255, 0)
origin = (0, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2

def apply_timestamp(shared_value, request):
     timestamp = time.strftime("%Y-%m-%d %X")
     total_pressue = shared_value[0]
     static_pressue = shared_value[1]
     airspeed = shared_value[2]
     text = f"{timestamp} | Static: {static_pressue:.1f} Total: {total_pressue:.1f} | Airspeed: {airspeed:.1f}"
     with MappedArray(request, "main") as m:
          cv2.putText(m.array,text,origin,font,scale,colour,thickness)

def start_recording(video_file, t0, pressure_data):
     picam2 = Picamera2()
     h264_encoder = H264Encoder()
     try:
          # Configure once
          video_config = picam2.create_video_configuration(main={"size": (1920, 1080), "format": "XBGR8888" }, transform=Transform(hflip=1, vflip=1))
          picam2.video_configuration.controls.FrameRate = 30
          picam2.configure(video_config)

          #picam2.pre_callback = apply_timestamp
          picam2.pre_callback = partial(apply_timestamp, pressure_data)

          # Start recording once
          print(f"[CAMERA] Starting recording to {video_file}")
          picam2.start_recording(h264_encoder, video_file, quality=Quality.VERY_HIGH)

          # Run until stop signal (for now, fixed duration)
          while True:
               time.sleep(1)
               os.sync()

     except Exception as e:
          print(f"Camera error: {e}")
     finally:
          print("[CAMERA] Stopping recording and releasing camera")
          try:
               picam2.stop_recording()
          except Exception as e:
               print(f"Error while stopping: {e}")
          picam2.close()

def check_file_size(file_path):
     if file_path.exists():
          return file_path.stat().st_size
     else:
          print("File doesn't exist")
          return 0


if __name__ == "__main__":
     t0 = time.monotonic()
     filename = "test.h264"
     start_recording(filename,t0)