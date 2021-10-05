import os
os.environ["GPIOZERO_PIN_FACTORY"] = "pigpio"

from enum import Enum
from gpiozero import AngularServo

ON_ANGLE = 70
OFF_ANGLE = 85
STATE_FILE = "lamp_switch.state"


class State(Enum):
    ON = 1
    OFF = 2


class Switch:
    def __init__(self):
        self._state = self._read_state()
        self._servo = AngularServo(14, initial_angle=ON_ANGLE if self._state == State.ON else OFF_ANGLE)

    def on(self):
        self._state = State.ON
        self._servo.angle = ON_ANGLE
        self._write_state()

    def off(self):
        self._state = State.OFF
        self._servo.angle = OFF_ANGLE
        self._write_state()

    def toggle(self):
        self.on() if self._state == State.OFF else self.off()

    def _read_state(self):
        try:
            with open(STATE_FILE, "r") as state_file:
                return State.ON if state_file.read() == "ON" else State.OFF
        except:
            return State.OFF

    def _write_state(self):
        with open(STATE_FILE, "w+") as state_file:
            state_file.write("ON" if self._state == State.ON else "OFF")