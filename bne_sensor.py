import time
import board
import busio
import adafruit_bme280.advanced as adafruit_bme280

i2c = busio.I2C(board.SCL, board.SDA)
bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
bme.sea_level_pressure = 1013.25


def run_sensor():
     while True:
          print("Running bne_sensor")
          print(f"Temp: {bme.temperature:.2f} °C")
          print(f"Pressure: {bme.pressure:.2f} hPa")
          print(f"Humidity: {bme.humidity:.2f} %")
          print(f"Altitude: {bme.altitude:.2f} m")
          print("-" * 30)
          time.sleep(1)

def dummy_print():
     while True:
          print("Ran BNE sensor file...")
          time.sleep(1)

if __name__ == "__main__":
    run_sensor()
