import time
import socket
from picamera2.encoders import H264Encoder, Quality
from picamera2 import Picamera2, MappedArray
from picamera2.outputs import PyavOutput
import os
import cv2
from libcamera import Transform
from functools import partial

WIDTH = 1920
HEIGHT = 1080
lores_WIDTH = 1280
lores_HEIGHT = 720
colour = (0, 255, 0)
origin_tl = (0, 30)
origin_bl = (10,HEIGHT-10)
origin_lores = (5,lores_HEIGHT-5)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2
colour_lores = 255

def apply_timestamp(shared_value, T0, request):
     """
     Apply a function an every incoming frame from the picam.
     shared_value is a python list of the shared memory between processes.
     """
     #timestamp = time.strftime("%Y-%m-%d %X")
     elapsed_time = time.monotonic() - T0
     total_pressue = shared_value[0]
     static_pressue = shared_value[1]
     airspeed = shared_value[2]
     text = f"T+ {elapsed_time:.1f}s | Static: {static_pressue:.1f} Total: {total_pressue:.1f} | Airspeed: {airspeed:.1f}"
     with MappedArray(request, "main") as m:
          cv2.putText(m.array,text,origin_bl,font,scale,colour,thickness)
     
     with MappedArray(request, "lores") as m:
          y_plane = m.array[0:lores_HEIGHT,0:lores_WIDTH]
          cv2.putText(y_plane,text,origin_lores,font,scale,colour_lores,thickness)

def check_mediamtx(host="127.0.0.1", port=8554):
     """
     Check whether the mediamtx service is up before starting the output from the camera.
     """
     try:
          with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
               sock.settimeout(0.5)
               result = sock.connect_ex((host,port))
               return not result
     except Exception as e:
          print(f"Error: {e}")
          return 0

def start_recording(video_file, t0, pressure_data):
     picam2 = Picamera2()
     h264_encoder = H264Encoder()
     stream_encoder = H264Encoder(bitrate=800000, profile='baseline')
     try:
          # Setup the RTSP output for MediaMTX
          #stream_output = PyavOutput("rtsp://127.0.0.1:8554/cam",format="rtsp")

          # Configure camera with 1080p for SD card save and lores for streaming
          video_config = picam2.create_video_configuration(main={"size": (WIDTH, HEIGHT), "format": "XBGR8888" },
          lores={"size": (1280, 720),"format": "YUV420"},
          transform=Transform(hflip=1, vflip=1))
          picam2.video_configuration.controls.FrameRate = 27
          picam2.configure(video_config)

          # Add the callback function to run on every frame
          initial_time = time.monotonic()
          picam2.pre_callback = partial(apply_timestamp, pressure_data, initial_time)

          # Start recording once
          print(f"[CAMERA] Starting recording to {video_file}")
          picam2.start_recording(h264_encoder, video_file, quality=Quality.VERY_HIGH)
          #picam2.start_recording(stream_encoder, stream_output, quality=Quality.LOW)

          # Run until stop signal (for now, fixed duration)
          stream_active = False
          while True:
               if not stream_active:
                    if check_mediamtx():
                         print("[CAMERA] MediaMTX detected. Starting stream...")
                         try:
                              stream_output = PyavOutput("rtsp://127.0.0.1:8554/cam",format="rtsp")
                              picam2.start_recording(stream_encoder, stream_output, name="lores")
                              stream_active = True
                         except Exception as e:
                              print(f"[CAMERA] Failed to attach stream to MediaMTX.: {e}")

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


if __name__ == "__main__":
     t0 = time.monotonic()
     pressure_data = [0,0.1,0.2]
     filename = "test.h264"
     start_recording(filename,t0,pressure_data)