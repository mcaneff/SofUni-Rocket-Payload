import time
import board
import busio
import queue 
from  adafruit_bme280 import basic as adafruit_bme280

def init_sensor():
     try:
          i2c = busio.I2C(board.SCL, board.SDA)
          bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
          bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
          return (bme1, bme2)
     except Exception as e:
          print("Sensor init failed:", e)
          return None


def run_sensor(event_q=None):
     try:
          i2c = busio.I2C(board.SCL, board.SDA)
          bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
          bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
          # if event_q:
          #      event_q.put("SENSOR_READY")

          while True:
               print("BME1                  BME2")
               print(f"Temp BME1: {bme1.temperature:.2f} °C         {bme2.temperature:.2f} °C")
               print(f"Pressure:  {bme1.pressure:.2f} hPa       {bme2.pressure:.2f} hPa")
               print(f"Humidity:  {bme1.humidity:.2f} %          {bme2.humidity:.2f} %")
               print(f"Altitude:  {bme1.altitude:.2f} m         {bme2.altitude:.2f} m")
               print("-"*30)
               time.sleep(1)

     except Exception as e:
          print(f"Sensor error: {e}")
          if event_q:
               event_q.put("SENSOR_FAIL")

if __name__ == "__main__":
     run_sensor()
