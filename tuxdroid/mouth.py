"""Module defining TuxDroid Mouth"""
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import types

from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidMouthError


# Bounce time for rising edge detection: 100ms
BOUNCE_TIME = 0.1
# TODO Improve button bounce time
BUTTON_BOUNCE_TIME = 0.25


class Mouth():
    """Mouth Component

    .. todo:: Missing head speed control (using PWM, need to find PWN frequency/duty cycle)
    """
    def __init__(self, head, config: dict):
        # Get logger
        self._logger = logging.getLogger("tuxdroid").getChild("head").getChild("mouth")
        # Set attributes
        self._head = head
        self.is_ready = False
        self.is_moving = False
        self.is_calibrated = False
        self.position = None
        # Privates
        self._count = 0
        self._motor_start_time = None
        self._gpio_names = ('opened_sensor', 'closed_sensor', 'motor')
        # Validate config
        self.config = config
        self._check_config()
        # Set GPUIO
        GPIO.setmode(GPIO.BCM)
        self._opened_sensor = int(config.get("gpio").get('opened_sensor'))
        GPIO.setup(self._opened_sensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._closed_sensor = int(config.get("gpio").get('closed_sensor'))
        GPIO.setup(self._closed_sensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Callbacks
        self._opened_callbacks = set()
        self._closed_callbacks = set()
        # Thread pool
        self._thread_pool = ThreadPoolExecutor()
        # we need to call calibrate() which is done by head component

    def _check_config(self):
        """Validate config"""
        if not self.config.get('gpio'):
            raise TuxDroidMouthError("Missing `gpio` section in mouth config")
        for gpio_name in self._gpio_names:
            if gpio_name not in self.config.get('gpio'):
                raise TuxDroidMouthError("Missing `%s` section in `gpio` section "
                                         "in mouth config", gpio_name)
            try:
                int(self.config.get('gpio').get(gpio_name))
            except ValueError:
                raise TuxDroidMouthError("`gpio.%s` should be a integer", gpio_name)

    def _set_callbacks(self):
        """Set button callbacks"""
        GPIO.remove_event_detect(self._opened_sensor)
        GPIO.add_event_detect(self._opened_sensor, GPIO.RISING,
                              callback=self._opened_event,
                              bouncetime=int(BUTTON_BOUNCE_TIME * 1000))
        GPIO.remove_event_detect(self._closed_sensor)
        GPIO.add_event_detect(self._closed_sensor, GPIO.RISING,
                              callback=self._closed_event,
                              bouncetime=int(BUTTON_BOUNCE_TIME * 1000))

    def _opened_event(self, gpio_id):
        """Opened mouth event callback"""
        # We have to not consider the first event
        if time.time() - self._motor_start_time < 0.2:
            # Maybe we want a debug ?
            self._logger.warning("Startup wings event detected, ignoring it")
            return

        # Check if the gpio_id is correct
        if gpio_id != self._opened_sensor:
            self._logger.error("Bad opened sensor GPIO id")
            raise TuxDroidMouthError("Bad GPIO id when opening")

        self.position = "OPENED"
        self._count += 1
        for callback in self._opened_callbacks:
            self._logger.debug("Calling: %s", callback.__name__)
            self._thread_pool.submit(callback)

    def _closed_event(self, gpio_id):
        """Closed mouth event callback"""
        # We have to not consider the first event
        if time.time() - self._motor_start_time < 0.2:
            # Maybe we want a debug ?
            self._logger.warning("Startup wings event detected, ignoring it")
            return

        # Check if the gpio_id is correct
        if gpio_id != self._closed_sensor:
            self._logger.error("Bad closed sensor GPIO id")
            raise TuxDroidMouthError("Bad GPIO id when closing")

        self.position = "CLOSED"
        self._count += 1
        for callback in self._closed_callbacks:
            self._logger.debug("Calling: %s", callback.__name__)
            self._thread_pool.submit(callback)

    def add_callback(self, position: str, callback):
        """Add callback"""
        if position not in ("closed", "opened"):
            raise TuxDroidMouthError("Bad position, should be 'closed' or 'opened'")
        if not isinstance(callback, types.FunctionType):
            raise TuxDroidMouthError("Callback `%s` is not a function", callback)

        callbacks = getattr(self, "_{}_callbacks".format(position))
        if callback in callbacks:
            self._logger.warning("Callback `%s` already registered to `%s` mouth",
                                 callback.__name__, position)
        else:
            self._logger.info("Adding callback `%s` to `%s` mouth", callback.__name__, position)
            callbacks.add(callback)

    def del_callback(self, position: str, callback):
        """Delete callback"""
        if position not in ("closed", "opened"):
            raise TuxDroidMouthError("Bad position, should be 'closed' or 'opened'")

        callbacks = getattr(self, "_{}_callbacks".format(position))
        if callback not in callbacks:
            self._logger.warning("Callback `%s` not registered to `%s` mouth",
                                 callback.__name__, position)
        else:
            self._logger.info("Deleting callback `%s` to `%s` mouth", callback.__name__, position)
            callbacks.remove(callback)

    def calibrate(self):
        """Moving mouth until it reaches the closed positiion"""
        # Calibration
        self._logger.info("Mouth calibration starting")
        # Init variables
        mouth_nb_moves = 0
        # Start moving
        self.start()
        # Start init
        while mouth_nb_moves < 2:
            # Wait for Rising edge
            GPIO.wait_for_edge(self._closed_sensor, GPIO.RISING)
            mouth_nb_moves += 1
        # Set position
        self.position = "CLOSED"
        # Stop moving
        self.stop()
        # Mouth should be closed
        self.is_calibrated = True
        self._logger.info("Mouth calibration done")
        # Set callbacks
        self._set_callbacks()
        # Set it as ready
        self.is_ready = True

    def set_position(self, position):
        """Move mouth to a position"""
        position = position.upper()
        if position not in ["OPENED", "CLOSED"]:
            self._logger.error("Bad mouth position")
            raise TuxDroidMouthError("Bad mouth position")
        # Do nothing if already in position
        if self.position == position:
            self._logger.info("Mouth already in %s position", position)
            return
        # Start moving
        self.start()
        # Wait for position
        # TODO add timeout
        while self.position != position:
            pass
        # Stop moving
        self.stop()

    def close(self):  # pylint: disable=C0103
        """Move head up"""
        self._logger.info("close mouth")
        self.set_position("CLOSED")

    def open(self):
        """Move head down"""
        self._logger.info("Open mouth")
        self.set_position("OPENED")

    def move(self, times):
        """Move head `n` times

        The count is incremented each time head are in OPENED or CLOSED position
        """
        self._count = 0
        # Start moving
        self.start()
        while self._count != times:
            # Wait for the count
            pass
        # Stop moving
        self.stop()
        self._count = 0

    def stop(self):
        """Stop moving mouth"""
        self._head.stop("mouth")

    def start(self):
        """Start moving mouth"""
        self._head.start("mouth")
