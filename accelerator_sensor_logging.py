import smbus2
import time
import struct
import csv
from datetime import datetime
import math

ACCELERATOR_FLIGHT_LOG = f"accelerator_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

class ICM20600:
     def __init__(self, address=0x68, bus=0):
          self.bus = smbus2.SMBus(bus)
          self.addr = address
          # Wake up device (disable sleep)
          self.bus.write_byte_data(self.addr, 0x6B, 0x00)
          # Configure accelerometer ±16g
          self.bus.write_byte_data(self.addr, 0x1C, 0x18)
          # Configure gyroscope ±2000°/s (bits 4:3 = 11)
          self.bus.write_byte_data(self.addr, 0x1B, 0x18)


     def read_accel(self):
          # Read 6 bytes starting at ACCEL_XOUT_H
          data = self.bus.read_i2c_block_data(self.addr, 0x3B, 6)
          ax, ay, az = struct.unpack('>hhh', bytes(data))
          # Sensitivity: 8192 LSB/g for ±4g range
          ax = ax / 2048.0 * 9.80665
          ay = ay / 2048.0 * 9.80665
          az = az / 2048.0 * 9.80665
          return ax, ay, az

     def read_gyro(self):
          # Read 6 bytes starting at GYRO_XOUT_H
          data = self.bus.read_i2c_block_data(self.addr, 0x43, 6)
          gx, gy, gz = struct.unpack('>hhh', bytes(data))
          # Sensitivity: 16.4 LSB/(°/s) for ±2000°/s
          gx = gx / 16.4 * math.pi / 180.0
          gy = gy / 16.4 * math.pi / 180.0
          gz = gz / 16.4 * math.pi / 180.0
          return gx, gy, gz


def record_acceleration_data(acc_file,T0):
     imu = ICM20600()
     print("Reading accelerometer data... Press Ctrl+C to stop.")

     with open(acc_file, 'w', newline="") as f:
          f.write("t_monotonic,ax_m_s2,ay_m_s2,az_m_s2,gx_rad_s,gy_rad_s,gz_rad_s\n")
          flush_every = 500
          buffer = []

          try:
               while True:
                    elapsed = time.monotonic() - T0
                    ax, ay, az = imu.read_accel()
                    gx, gy, gz = imu.read_gyro()
                    line = f"{elapsed:.6f},{ax:.4f},{ay:.4f},{az:.4f},{gx:.4f},{gy:.4f},{gz:.4f}\n"
                    buffer.append(line)

               if len(buffer) >= flush_every:
                    f.writelines(buffer)
                    f.flush()
                    buffer.clear()
          except KeyboardInterrupt:
               print("\nStopped.")

if __name__ == "__main__":
     start_time = time.monotonic()
     record_acceleration_data(ACCELERATOR_FLIGHT_LOG,start_time)