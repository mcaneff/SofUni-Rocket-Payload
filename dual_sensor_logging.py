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
               b.overscan_pressure = 1     # lowest oversampling
               # b.overscan_temperature = 0  # disable temp
               # b.overscan_humidity = 0     # disable humidity
               b.filter = 0                # no IIR filter

          return (bme1, bme2)
     except Exception as e:
          print("Sensor init failed:", e)
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
               b.overscan_pressure = 1
               # b.overscan_temperature = 1
               # b.overscan_humidity = 1
               b.filter = 0
          
          # Open CSV file for logging
          with open("bme280_flight_log.csv", "w") as f:
               # Write header
               f.write("elapsed_time,"
                    "tempC_1, pressure_hPa_1, humidity_pct_1, alt_m_1,"
                    "tempC_2, pressure_hPa_2, humidity_pct_2, alt_m_2\n")
               
               count = 0
               buffer = []

               while True:
                    elapsed = time.monotonic() - T0

                    # Read pressure only (fastest possible)
                    p1 = bme1.pressure
                    p2 = bme2.pressure

                    # Build CSV line
                    line = f"{elapsed:.6f},{p1:.2f},{p2:.2f}\n"
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
