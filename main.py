import multiprocessing as mp
import bne_sensor
import dual_sensor_logging
import camera_module
import accelerator_sensor_logging
from fsm import State, Event, next_state
from gpiozero import Button , LED
import time
from datetime import datetime
import signal


# Setup GPIO17 as input (BCM numbering)
go_signal = Button(26, pull_up=False, bounce_time=0.05)
HEARTBEAT_LED = LED(17)
HEARTBEAT_LED_FREQ = 0.5
countDownTime = 0 # Time to wait until start sec)

# Generate unique filename with timestamp
FLIGHT_LOG_FILE = f"bme280_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
CAMERA_VIDEO_FILE = f"camera_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
ACCELERATOR_FLIGHT_LOG = f"accelerator_flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

class ServiceExit(Exception):
    pass

def service_shutdown(signum, frame):
    print(f"Caught signal {signum}, initiating graceful shutdown...")
    raise ServiceExit

def init_and_check_sensors(state):
     sensors, sensors_offset = dual_sensor_logging.init_sensor()
     if sensors is not None:
          state = next_state(state, Event.INIT_DONE)
          print("Sensor alive →", state)
     else:
          state = next_state(state, Event.ERROR)
          print("Sensor failed →", state)
     return state, sensors_offset

def start_processes(t0, shared_data,pressure_offset):
    return {
        "camera": mp.Process(target=camera_module.start_recording, args=(CAMERA_VIDEO_FILE, t0, shared_data)),
        "sensor": mp.Process(target=dual_sensor_logging.run_sensor, args=(t0,shared_data,pressure_offset)),
        "imu": mp.Process(target=accelerator_sensor_logging.record_acceleration_data, args=(ACCELERATOR_FLIGHT_LOG, t0))
    }

def start_process(role, t0, shared_data,pressure_offset):
     if role == "camera":
          return mp.Process(target=camera_module.start_recording, args=(CAMERA_VIDEO_FILE, t0, shared_data))
     elif role == "sensor":
          return mp.Process(target=dual_sensor_logging.run_sensor, args=(t0, shared_data,pressure_offset))
     elif role == "imu":
          return mp.Process(target=accelerator_sensor_logging.record_acceleration_data, args=(ACCELERATOR_FLIGHT_LOG, t0))

def main():

     signal.signal(signal.SIGTERM, service_shutdown)

     state = State.BOOT
     procs = {
          "camera": None,
          "sensor": None,
          "imu": None
     }
     print(f"State: {state}")
     t0 = time.monotonic()
     print(f"Current Time: {t0}")
     led_on = False
     last_blink_time = time.monotonic()
     running = True
     sensors_offset = 0.0

     try:
          while running:
               if state == State.BOOT:
                    state, sensors_offset = init_and_check_sensors(state)
                    HEARTBEAT_LED.off()
                    # Create shared memory array for pressure data
                    pressure_data = mp.Array('f', [0.0,0.0,0.0])
               # video config here
               elif state == State.PRIMED:
                    last_blink_time = time.monotonic()
                    if time.monotonic() >= t0 + countDownTime:
                         state = next_state(state, Event.START_RECORDING)
                         print("Time Begin Recording")
                    if go_signal.is_pressed:  # HIGH detected
                         print("GO signal received → Recording")
                         state = next_state(state, Event.START_RECORDING)

               elif state == State.RECORDING:
                    # Heartbeat blink
                    if time.monotonic() - last_blink_time >= HEARTBEAT_LED_FREQ:
                         led_on = not led_on
                         HEARTBEAT_LED.value = led_on
                         last_blink_time = time.monotonic()

                    # Start processes if not running
                    if not all(procs.values()):  # at least one None
                         procs = start_processes(t0, pressure_data,sensors_offset)
                         for name, p in procs.items():
                              p.start()
                              print(f"Started {name} process (PID {p.pid})")
                         last_restart = {name: 0 for name in procs}

                    # Supervise & restart if needed
                    for name, p in list(procs.items()):
                         if not p.is_alive() and time.monotonic() - last_restart[name] > 2:
                              print(f"[ERROR] {name} process died → restarting...")
                              new_p = start_process(name, t0, pressure_data,sensors_offset)
                              new_p.start()
                              procs[name] = new_p
                              last_restart[name] = time.monotonic()

               elif state == State.TOUCHDOWN:
                    running = False
                    print("→", state)
               
               elif state == State.FAIL:
                    running = False
                    print("→", state)

     except KeyboardInterrupt:
          print("Manual stopping initiated...")
          
     except ServiceExit:
          print("Systemd stop detected...")

     finally:
          print("Cleaning up before exit...")
          for p in procs.values():
               if p is not None and p.is_alive():
                    p.terminate()
                    p.join()
               HEARTBEAT_LED.off()
          state = next_state(state, Event.MISSION_END)



if __name__ == "__main__":
     main()
