import time
import board
import busio
import adafruit_bme280.advanced as adafruit_bme280
from datetime import datetime
from picamera2.encoders import H264Encoder, Quality
from picamera2 import Picamera2
from gpiozero import LED
import os
from pathlib import Path

# Generate unique filename with timestamp
FLIGHT_LOG_FILE = f"bme280_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
CAMERA_VIDEO_FILE = f"camera_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
CAMERA_LED_PIN = 26

def init_sensor():
     try:
          i2c = busio.I2C(board.SCL, board.SDA)
          bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
          bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
          
          # Fastest mode for both sensors
          for b in (bme1, bme2):
               b.mode = adafruit_bme280.MODE_FORCE
               b.overscan_pressure = 1
               b.filter = 0
          
          # Read baseline environmental conditions
          time.sleep(0.1)  # Allow sensors to stabilize
          t1, t2 = bme1.temperature, bme2.temperature
          p1, p2 = bme1.pressure, bme2.pressure
          h1, h2 = bme1.humidity, bme2.humidity
          a1, a2 = bme1.altitude, bme2.altitude
          
          # Create/overwrite CSV with header and baseline data
          with open(FLIGHT_LOG_FILE, "w") as f:
               f.write("elapsed_time,pressure_hPa_1,pressure_hPa_2,tempC_1,tempC_2,humidity_1,humidity_2,altitude1,altitude2\n")
               f.write(f"0.000000,{p1:.3f},{p2:.3f},{t1:.2f},{t2:.2f},{h1:.2f},{h2:.2f},{a1:.2f},{a2:.2f}\n")
          
          print(f"Baseline recorded: T1={t1:.2f}°C T2={t2:.2f}°C H1={h1:.2f}% H2={h2:.2f}%")
          print(f"Logging to: {FLIGHT_LOG_FILE}")
          
          # Gracefully close I2C to free resources
          i2c.deinit()
          print("I2C closed, resources freed")
          
          return (bme1, bme2)  # Return tuple to signal success (sensors no longer usable)
          
     except Exception as e:
          print("Sensor init failed:", e)
          if i2c:
               try:
                    i2c.deinit()
               except:
                    pass
          return None


def run_sensor(T0, event_q=None):
     try:
          # Initialize sensors
          i2c = busio.I2C(board.SCL, board.SDA)
          bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
          bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
          
          # Fastest mode for both sensors
          for b in (bme1, bme2):
               b.mode = adafruit_bme280.MODE_FORCE
               b.overscan_pressure = 1  # Minimum oversampling for speed
               b.filter = 0              # No filtering for speed
          
          # Append to existing CSV file (baseline already written by init_sensor)
          with open(FLIGHT_LOG_FILE, "a") as f:
               count = 0
               buffer = []

               while True:
                    elapsed = time.monotonic() - T0

                    # Read pressure only (fastest possible)
                    p1 = bme1.pressure
                    p2 = bme2.pressure

                    # Build CSV line
                    line = f"{elapsed:.6f},{p1:.3f},{p2:.3f},,,,,\n"
                    buffer.append(line)

                    count += 1

                    # Print heartbeat every 200 samples
                    if count % 200 == 0:
                         print(f"T+{elapsed:.1f}s | Samples: {count}")

                    # Flush to disk every 500 samples
                    if len(buffer) >= 500:
                         f.writelines(buffer)
                         f.flush()
                         buffer.clear()

     except Exception as e:
          print(f"Sensor error: {e}")
          if event_q:
               event_q.put("SENSOR_FAIL")

def start_recording(video_file):
    picam2 = Picamera2()
    h264_encoder = H264Encoder()
    try:
         video_config = picam2.create_video_configuration()
         picam2.configure(video_config)
         picam2.video_configuration.controls.FrameRate = 30
         picam2.start_recording(h264_encoder,video_file,quality=Quality.VERY_HIGH)
         while True:
              time.sleep(1)
    except Exception as e:
         print("Camera error: {e}")
    finally:
         try:
              picam2.stop_recording()
              print("Camera recording stopped.")
         except Exception as e:
              print(f"Error stopping camera {e}")
    picam2.close()
    print("Camera closed and resources released")
    
def check_file_size(file_path):
    if file_path.exists():
        return file_path.stat().st_size
    else:
        print("File doesn't exist")
        return 0

def camera_activity_led(camera_file,led_pin):
    ''' Blink CAMERA_LED_PIN based on video file.'''
    camera_led = LED(led_pin)
    file_path = Path(camera_file)
    max_file_size = 0
    try:
        while True:
            current_size = check_file_size(file_path)
            if current_size > max_file_size:
                max_file_size = current_size
                camera_led.blink(on_time=0.5,off_time=0.5)
                time.sleep(1)
            else:
                camera_led.off()
                time.sleep(0.5)
    except Exception as e:
         print(f"LED process error: {e}")

    finally:
         camera_led.off()
         print("Releasing LED.")

if __name__ == "__main__":
     run_sensor(time.monotonic())
