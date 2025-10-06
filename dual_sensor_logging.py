import time
import board
import busio
import adafruit_bme280.advanced as adafruit_bme280


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
          
          # Create/overwrite CSV with header and baseline data
          with open("bme280_flight_log.csv", "w") as f:
               f.write("elapsed_time,pressure_hPa_1,pressure_hPa_2,tempC_1,tempC_2,humidity_1,humidity_2\n")
               f.write(f"0.000000,{p1:.3f},{p2:.3f},{t1:.2f},{t2:.2f},{h1:.2f},{h2:.2f}\n")
          
          print(f"Baseline recorded: T1={t1:.2f}°C T2={t2:.2f}°C H1={h1:.2f}% H2={h2:.2f}%")
          
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
          with open("bme280_flight_log.csv", "a") as f:
               count = 0
               buffer = []

               while True:
                    elapsed = time.monotonic() - T0

                    # Read pressure only (fastest possible)
                    p1 = bme1.pressure
                    p2 = bme2.pressure

                    # Build CSV line
                    line = f"{elapsed:.6f},{p1:.3f},{p2:.3f},,,\n"
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


if __name__ == "__main__":
     run_sensor(time.monotonic())
