"""Module for faking GPIO library"""
# pylint: disable=C0103
from concurrent.futures import ThreadPoolExecutor
# from unittest.mock import MagicMock
import time

try:
    import RPi.GPIO as _RealGPIO
    FAKE_GPIO = False
except RuntimeError:
    FAKE_GPIO = True


class _FakeGPIO():
    """Fake GPIOs plugged into tuxdroid body"""

    BCM = None
    IN = None
    OUT = None
    PUD_UP = None
    LOW = 0
    HIGH = 1
    RISING = 1
    FALLING = 0

    def __init__(self):
        self._thread_pool = ThreadPoolExecutor()
        self.config = {}
        self.callbacks = {}
        self.waits = {self.RISING: {},
                      self.FALLING: {},
                      }

    def set_config_(self, config):
        """Save config"""
        self.config = config

    def _wings_start(self):
        """Simulate wings move"""
        self._run_wings = True
        moving_sensor_gpio = self.config.get('wings', {}).get('gpio', {}).get('moving_sensor', {})
        while self._run_wings:
            # Wings moving sensor edge rising
            self.waits[self.RISING][moving_sensor_gpio] = True
            # Wings moving sensor callback
            callback = self.callbacks.get(moving_sensor_gpio)
            if callback:
                func = callback.get(self.RISING)
                if func:
                    func(moving_sensor_gpio)
            # Wait for next up
            time.sleep(0.3)
            # stop the move if asked
            if not self._run_wings:
                break
            # Wings moving sensor edge rising
            self.waits[self.RISING][moving_sensor_gpio] = True
            # Wings moving sensor callback
            callback = self.callbacks.get(moving_sensor_gpio)
            if callback:
                func = callback.get(self.RISING)
                if func:
                    func(moving_sensor_gpio)
            # Wait for next down
            time.sleep(0.5)

    def _wings_stop(self):
        """Simulate stop moving wings"""
        self._run_wings = False

    def _mouth_start(self):
        """Simulate start moving mouth"""
        self._run_mouth = True
        opened_sensor_gpio = self.config.get('head', {}).get('mouth', {}).\
            get('gpio', {}).get('opened_sensor', {})
        closed_sensor_gpio = self.config.get('head', {}).get('mouth', {}).\
            get('gpio', {}).get('closed_sensor', {})
        while self._run_mouth:
            print("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
            # Wings moving sensor edge rising
            self.waits[self.RISING][opened_sensor_gpio] = True
            # Wings moving sensor callback
            callback = self.callbacks.get(opened_sensor_gpio)
            if callback:
                func = callback.get(self.RISING)
                if func:
                    func(opened_sensor_gpio)
            # Wait for next up
            time.sleep(0.5)
            # stop the move if asked
            if not self._run_mouth:
                break
            # Wings moving sensor edge rising
            self.waits[self.RISING][closed_sensor_gpio] = True
            # Wings moving sensor callback
            callback = self.callbacks.get(closed_sensor_gpio)
            if callback:
                func = callback.get(self.RISING)
                if func:
                    func(closed_sensor_gpio)
            # Wait for next down
            time.sleep(0.5)

    def _mouth_stop(self):
        """Simulate stop moving mouth"""
        self._run_mouth = False

    def _eyes_start(self):
        """Simulate stop moving mouth"""
        self._run_eyes = True
        opened_sensor_gpio = self.config.get('head', {}).get('eyes', {}).\
            get('gpio', {}).get('opened_sensor', {})
        closed_sensor_gpio = self.config.get('head', {}).get('eyes', {}).\
            get('gpio', {}).get('closed_sensor', {})
        while self._run_eyes:
            # Wings moving sensor edge rising
            self.waits[self.RISING][opened_sensor_gpio] = True
            # Wings moving sensor callback
            callback = self.callbacks.get(opened_sensor_gpio)
            if callback:
                func = callback.get(self.RISING)
                if func:
                    func(opened_sensor_gpio)
            # Wait for next up
            time.sleep(0.3)
            # stop the move if asked
            if not self._run_eyes:
                break
            # Wings moving sensor edge rising
            self.waits[self.RISING][closed_sensor_gpio] = True
            # Wings moving sensor callback
            callback = self.callbacks.get(closed_sensor_gpio)
            if callback:
                func = callback.get(self.RISING)
                if func:
                    func(closed_sensor_gpio)
            # Wait for next down
            time.sleep(0.3)

    def _eyes_stop(self):
        """Simulate stop moving eyes"""
        self._run_eyes = False

    def setmode(self, mode):
        """Fake GPIO set mode"""
        pass

    def setup(self, channel, channel_type, pull_up_down=None):
        """Fake GPIO setup"""
        pass

    def add_event_detect(self, channel, event_type,
                         callback=None, bouncetime=0):  # pylint: disable=W0613
        """Add callback"""
        self.callbacks.setdefault(channel, {})
        self.callbacks[channel][event_type] = callback

    def remove_event_detect(self, channel):
        """Remove callback"""
        if channel in self.callbacks:
            self.callbacks.pop(channel)

    def wait_for_edge(self, channel, event_type):
        """Wait for new edge (rising or falling)"""
        self.waits[event_type][channel] = False
        while not self.waits[event_type][channel]:
            time.sleep(0.1)

    def cleanup(self):
        """Fake GPIO cleanup"""
        pass

    def output(self, channel, output_type):
        """Simulate set GPIO output"""
        wings_motor_gpio = self.config.get('wings', {}).get('gpio', {}).\
            get('motor_direction_1', {})
        mouth_motor_gpio = self.config.get('head', {}).get('mouth', {}).\
            get('gpio', {}).get('motor')
        eyes_motor_gpio = self.config.get('head', {}).get('eyes', {}).\
            get('gpio', {}).get('motor')
        if channel == wings_motor_gpio:
            # Simulate GPIO.output to simulate wings start or stop
            if output_type == self.HIGH:
                self._thread_pool.submit(self._wings_start)
            elif output_type == self.LOW:
                self._wings_stop()
        elif channel == mouth_motor_gpio:
            if output_type == self.HIGH:
                self._thread_pool.submit(self._mouth_start)
            elif output_type == self.LOW:
                self._mouth_stop()
        elif channel == eyes_motor_gpio:
            if output_type == self.HIGH:
                self._thread_pool.submit(self._eyes_start)
            elif output_type == self.LOW:
                self._eyes_stop()


# Set GPIO
if FAKE_GPIO:
    GPIO = _FakeGPIO()
else:
    GPIO = _RealGPIO
