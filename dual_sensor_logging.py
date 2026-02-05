import time
import board
import busio
import adafruit_bme280.advanced as adafruit_bme280
from datetime import datetime
from numba import njit
from math import sqrt

# Generate unique filename with timestamp
FLIGHT_LOG_FILE = f"bme280_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

@njit
def calculate_airspeed(p_total, p_static, rho=1.225 , sensor_offset=0):
     delta_p = ((p_total - p_static)-sensor_offset)*100
     return sqrt((2 * abs(delta_p))/rho)

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
          
          # Compile numba function before running sensor
          _ = calculate_airspeed(101325.0, 101320.0)

          # Create/overwrite CSV with header and baseline data
          with open(FLIGHT_LOG_FILE, "w") as f:
               f.write("elapsed_time,pressure_hPa_1,pressure_hPa_2,tempC_1,tempC_2,humidity_1,humidity_2,altitude1,altitude2\n")
               f.write(f"0.000000,{p1:.3f},{p2:.3f},{t1:.2f},{t2:.2f},{h1:.2f},{h2:.2f},{a1:.2f},{a2:.2f}\n")
          
          print(f"Baseline recorded: T1={t1:.2f}°C T2={t2:.2f}°C H1={h1:.2f}% H2={h2:.2f}%")
          print(f"Logging to: {FLIGHT_LOG_FILE}")

          # Calibrate sensor offset
          start_time = time.monotonic()
          calibration_duration = 2
          offsets = []
          offset = 0
          while time.monotonic() - start_time < calibration_duration:
               p1, p2 = bme1.pressure, bme2.pressure
               offsets.append(p1-p2)
               time.sleep(0.05)
          
          if len(offsets) > 0:
               offset = sum(offsets) / len(offsets)
          print(f"The ORIGINAL offset is: {offset}")
          # Gracefully close I2C to free resources
          i2c.deinit()
          print("I2C closed, resources freed")
          
          return (bme1, bme2), offset  # Return tuple to signal success (sensors no longer usable)
          
     except Exception as e:
          print("Sensor init failed:", e)
          if i2c:
               try:
                    i2c.deinit()
               except:
                    pass
          return None


def run_sensor(T0, shared_data, sensor_offset, event_q=None):
     try:
          # Initialize sensors
          i2c = busio.I2C(board.SCL, board.SDA)
          bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
          bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)

          # Airspeed filtering
          ALPHA = 0.2
          smoothed_airspeed = 0.0
          
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
                    raw_airspeed = calculate_airspeed(p1,p2,sensor_offset=sensor_offset)
                    smoothed_airspeed = (ALPHA * raw_airspeed) + ((1 - ALPHA) * smoothed_airspeed)

                    shared_data[0] = p1
                    shared_data[1] = p2
                    shared_data[2] = smoothed_airspeed

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

                    time.sleep(0.01)

     except Exception as e:
          print(f"Sensor error: {e}")
          if event_q:
               event_q.put("SENSOR_FAIL")


if __name__ == "__main__":
     run_sensor(time.monotonic())
