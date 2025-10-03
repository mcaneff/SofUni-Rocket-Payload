from enum import Enum, auto

# Define the possible states
class State(Enum):
    BOOT = auto()
    PRIMED = auto()
    RECORDING = auto()
    TOUCHDOWN = auto()
    FAIL = auto()

# Define possible events
class Event(Enum):
    INIT_DONE = auto()
    START_RECORDING = auto()
    MISSION_END = auto()
    ERROR = auto()

# Define the transition table
TRANSITIONS = {
     State.BOOT: {
          Event.INIT_DONE: State.PRIMED
     },
     State.PRIMED: {
          Event.START_RECORDING: State.RECORDING,
          Event.ERROR: State.FAIL
     },
     State.RECORDING: {
          Event.MISSION_END: State.TOUCHDOWN,
          Event.ERROR: State.FAIL
     },
     State.FAIL: {
          Event.MISSION_END: State.TOUCHDOWN
     }
}

# Transition function
def next_state(current: State, event: Event) -> State:
     """Move to the next state based on current state and event."""
     return TRANSITIONS.get(current, {}).get(event, current)

# Example usage
if __name__ == "__main__":
     state = State.BOOT
     print("Start:", state)

     # Simulate mission
     state = next_state(state, Event.INIT_DONE)
     print("After init:", state)

     state = next_state(state, Event.START_RECORDING)
     print("After start:", state)

     state = next_state(state, Event.MISSION_END)
     print("After mission:", state)
