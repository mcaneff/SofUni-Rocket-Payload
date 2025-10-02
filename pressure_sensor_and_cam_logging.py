import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280
from picamera2 import Picamera2


i2c = busio.I2C(board.SCL, board.SDA)

# Two sensors at different addresses
bme1 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
bme2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)

# Fastest mode (lowest oversampling, no filter)
for b in (bme1, bme2):
    b.overscan_pressure = 1
    b.overscan_temperature = 1
    b.overscan_humidity = 1
    b.filter = 0


picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080)},      # resolution
    controls={"FrameRate": 30}        # frame rate
)
picam2.configure(video_config)
picam2.start_recording("output_video.mp4")


with open("bme280_dual_log.csv", "w") as f:
    f.write("timestamp,"
            "tempC_1,pressure_hPa_1,humidity_pct_1,alt_m_1,"
            "tempC_2,pressure_hPa_2,humidity_pct_2,alt_m_2\n")

    print("Logging merged sensor data + recording video... (Ctrl+C to stop)")
    count = 0
    start_time = time.perf_counter()

    try:
        while True:
            now = time.perf_counter()

            # Sensor 1
            t1 = bme1.temperature
            p1 = bme1.pressure
            h1 = bme1.humidity
            a1 = bme1.altitude

            # Sensor 2
            t2 = bme2.temperature
            p2 = bme2.pressure
            h2 = bme2.humidity
            a2 = bme2.altitude

            f.write(f"{now:.6f},"
                    f"{t1:.2f},{p1:.2f},{h1:.2f},{a1:.2f},"
                    f"{t2:.2f},{p2:.2f},{h2:.2f},{a2:.2f}\n")

            count += 1
            if count % 200 == 0:
                f.flush()

    except KeyboardInterrupt:
        elapsed = time.perf_counter() - start_time
        print(f"\nStopped. Rows collected: {count}, duration: {elapsed:.2f}s")

    finally:
        picam2.stop_recording()
