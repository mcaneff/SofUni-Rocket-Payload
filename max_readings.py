import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

# Optional: set oversampling to minimum for fastest data rate
bme.overscan_pressure = 1
#bme.overscan_temperature = 1
#bme.overscan_humidity = 1
bme.filter = 0

print("Measuring effective sample rate... (Ctrl+C to stop)")

last_time = time.perf_counter()
count = 0
start_time = last_time

try:
    while True:
        # Take a reading
#        temp = bme.temperature
        pres = bme.pressure
#        hum = bme.humidity

        # Time measurement
        now = time.perf_counter()
        dt = now - last_time
        last_time = now

        # Compute instantaneous frequency
        hz = 1.0 / dt if dt > 0 else 0

#        print(f"{count:05d} | Δt={dt*1000:.2f} ms | {hz:.1f} Hz | "
#              f"T={temp:.2f}°C P={pres:.2f}hPa H={hum:.2f}%")

        count += 1

except KeyboardInterrupt:
    total_time = time.perf_counter() - start_time
    avg_rate = count / total_time if total_time > 0 else 0
    print("\nStopped.")
    print(f"Total samples: {count}")
    print(f"Average rate: {avg_rate:.1f} Hz")
