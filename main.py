import multiprocessing as mp
import bne_sensor
import dual_sensor_logging
from fsm import State, Event, next_state
from gpiozero import Button
import time


# Setup GPIO17 as input (BCM numbering)
go_signal = Button(17, pull_up=False, bounce_time=0.05)
countDownTime = 1 # Time to wait until start sec)

def init_and_check_sensors(state):
     sensors = dual_sensor_logging.init_sensor()
     if sensors is not None:
          state = next_state(state, Event.INIT_DONE)
          print("Sensor alive →", state)
     else:
          state = next_state(state, Event.ERROR)
          print("Sensor failed →", state)
     return state

def main():
     state = State.BOOT
     procs = []
     print(f"State: {state}")
     t0 = time.monotonic()
     print(f"Current Time: {t0}")
     running = True

     while running:
          if state == State.BOOT:
               state = init_and_check_sensors(state)
          
          elif state == State.PRIMED:
               if time.monotonic() >= t0 + countDownTime:
                    state = next_state(state, Event.START_RECORDING)
                    print("Time Begin Recording")
               if go_signal.is_pressed:  # HIGH detected
                    print("GO signal received → Recording")
                    state = next_state(state, Event.START_RECORDING)

          elif state == State.RECORDING:
               if not procs:
                    event_q = mp.Queue()
                    procs.append(mp.Process(target=bne_sensor.dummy_print ))
                    procs.append(mp.Process(target=dual_sensor_logging.run_sensor , args = (t0,)))
                    procs.append(mp.Process(target=dual_sensor_logging.start_recording, args=(dual_sensor_logging.CAMERA_VIDEO_FILE,)))
                    procs.append(mp.Process(target=dual_sensor_logging.camera_activity_led, args=(dual_sensor_logging.CAMERA_VIDEO_FILE,dual_sensor_logging.CAMERA_LED_PIN,)))
                    for p in procs:
                         p.start()
                    print("Processes started")
 
               try:
                    all_alive = all(p.is_alive() for p in procs)
                    if not all_alive:
                         val =1
                         # state = next_state(state, Event.ERROR)
                         # print("Process died →", state)
               except KeyboardInterrupt:
                    print("Stopping...")
                    for p in procs:
                         p.terminate()
                    state = next_state(state, Event.MISSION_END)

          elif state == State.TOUCHDOWN:
               running = False
               print("→", state)
          
          elif state == State.FAIL:
               running = False
               print("→", state)

if __name__ == "__main__":
     main()
