import time
import board
import busio

from datetime import datetime
from picamera2.encoders import H264Encoder, Quality
from picamera2 import Picamera2
from gpiozero import LED
import os
from pathlib import Path


def start_recording(video_file, t0):
     picam2 = Picamera2()
     h264_encoder = H264Encoder()
     try:
          # Configure once
          video_config = picam2.create_video_configuration(main={"size": (1920, 1080), "format": "XBGR8888"})
          picam2.configure(video_config)

          # Start recording once
          print(f"[CAMERA] Starting recording to {video_file}")
          picam2.start_recording(h264_encoder, video_file, quality=Quality.VERY_HIGH)

          # Run until stop signal (for now, fixed duration)
          while True:
               time.sleep(0.1)

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
     start_recording()