import multiprocessing as mp
import bne_sensor, both_sensors
from fsm import State, Event, next_state

def init_and_check_sensors(state):
     if bne_sensor.init_sensor():
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

     running = True
     while running:
          if state == State.BOOT:
               state = init_and_check_sensors(state)
          
          elif state == State.PRIMED:
               # Add a start mission condition
               state = next_state(state, Event.START_RECORDING)
               print("→", state)

          elif state == State.RECORDING:
               if not procs:
                    procs.append(mp.Process(target=bne_sensor.dummy_print))
                    procs.append(mp.Process(target=both_sensors.run_sensor))
                    for p in procs:
                         p.start()
                    print("Processes started")

               try:
                    all_alive = all(p.is_alive() for p in procs)
                    if not all_alive:
                         state = next_state(state, Event.ERROR)
                         print("Process died →", state)
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
