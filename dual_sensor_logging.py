import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280

def init_sensor():
     try:
          i2c = busio.I2C(board.SCL, board.SDA)
          bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
          bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
          
          # Fastest mode for both sensors
          for b in (bme1, bme2):
               b.overscan_pressure = 1
               b.overscan_temperature = 1
               b.overscan_humidity = 1
               b.filter = 0
          
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
               b.overscan_pressure = 1
               b.overscan_temperature = 1
               b.overscan_humidity = 1
               b.filter = 0
          
          # Open CSV file for logging
          with open("bme280_flight_log.csv", "w") as f:
               # Write header
               f.write("elapsed_time,"
                    "tempC_1,pressure_hPa_1,humidity_pct_1,alt_m_1,"
                    "tempC_2,pressure_hPa_2,humidity_pct_2,alt_m_2\n")
               
               count = 0
               
               while True:
                    elapsed = time.monotonic() - T0
                    
                    # Read Sensor 1
                    t1 = bme1.temperature
                    p1 = bme1.pressure
                    h1 = bme1.humidity
                    a1 = bme1.altitude
                    
                    # Read Sensor 2
                    t2 = bme2.temperature
                    p2 = bme2.pressure
                    h2 = bme2.humidity
                    a2 = bme2.altitude
                    
                    # Write to CSV
                    f.write(f"{elapsed:.6f},"
                         f"{t1:.2f},{p1:.2f},{h1:.2f},{a1:.2f},"
                         f"{t2:.2f},{p2:.2f},{h2:.2f},{a2:.2f}\n")
                    
                    count += 1
                    
                    # Flush every 200 readings for data safety
                    if count % 200 == 0:
                         f.flush()

     except Exception as e:
          print(f"Sensor error: {e}")
          if event_q:
               event_q.put("SENSOR_FAIL")


if __name__ == "__main__":
     run_sensor(time.monotonic())
