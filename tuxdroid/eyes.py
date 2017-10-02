"""Module defining TuxDroid Eyes"""
# pylint: disable=R0801
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import types

from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidEyesError


# Bounce time for rising edge detection: 100ms
BOUNCE_TIME = 0.1
# TODO Improve button bounce time
BUTTON_BOUNCE_TIME = 0.25


class Eyes():
    """Eyes Component

    .. todo:: Missing head speed control (using PWM, need to find PWN frequency/duty cycle)
    """
    def __init__(self, head, config: dict):
        # Get logger
        self._logger = logging.getLogger("tuxdroid").getChild("head").getChild("eyes")
        # Set attributes
        self._head = head
        self.is_ready = False
        self.is_moving = False
        self.is_calibrated = False
        self.led_right = None
        self.led_left = None
        self.position = None
        # Privates
        self._move_count = 0
        self._wanted_moves = None
        self._motor_start_time = None
        self._gpio_names = ('opened_sensor', 'closed_sensor', 'motor',
                            'left_led', 'right_led')
        # Validate config
        self.config = config
        self._check_config()
        # Set GPUIO
        GPIO.setmode(GPIO.BCM)
        self._opened_sensor = int(config.get("gpio").get('opened_sensor'))
        GPIO.setup(self._opened_sensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._closed_sensor = int(config.get("gpio").get('closed_sensor'))
        GPIO.setup(self._closed_sensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._right_led = int(config.get("gpio").get('right_led'))
        GPIO.setup(self._right_led, GPIO.OUT)
        self._left_led = int(config.get("gpio").get('left_led'))
        GPIO.setup(self._left_led, GPIO.OUT)
        # Callbacks
        self._opened_callbacks = set()
        self._closed_callbacks = set()
        # Thread pool
        self._thread_pool = ThreadPoolExecutor()
        # we need to call calibrate() which is done by head component

    def led_on(self, side: str = None):
        """Power on eye leds

        .. todo:: Add intensity support

        side: 'left', 'right' or None
              None means both leds
        """
        if side is None:
            # Power on left and right leds
            GPIO.output(self._right_led, GPIO.HIGH)
            GPIO.output(self._left_led, GPIO.HIGH)
            self.led_right = True
            self.led_left = True
        elif side not in ("right", "left"):
            raise TuxDroidEyesError("Bad side should be `right` or `left`")
        else:
            # Power on right or left led
            GPIO.output(getattr(self, '_{}_led'.format(side)), GPIO.HIGH)
            setattr(self, 'led_{}'.format(side), True)

    def led_off(self, side: str = None):
        """Power off eye leds

        side: 'left', 'right' or None
              None means both leds
        """
        if side is None:
            # Power off left and right leds
            GPIO.output(self._right_led, GPIO.LOW)
            GPIO.output(self._left_led, GPIO.LOW)
            self.led_right = False
            self.led_left = False
        elif side not in ("right", "left"):
            raise TuxDroidEyesError("Bad side should be `right` or `left`")
        else:
            # Power off right or left led
            GPIO.output(getattr(self, '_{}_led'.format(side)), GPIO.LOW)
            setattr(self, 'led_{}'.format(side), False)

    def led_blink(self, times: int, side: str = None):
        """Blink eye leds

        side: 'left', 'right' or None
              None means both leds
        """
        self.led_off(side)
        time.sleep(0.5)
        for _ in range(times):
            self.led_on(side)
            time.sleep(0.5)
            self.led_off(side)
            time.sleep(0.5)

    def _check_config(self):
        """Validate config"""
        if not self.config.get('gpio'):
            raise TuxDroidEyesError("Missing `gpio` section in eyes config")
        for gpio_name in self._gpio_names:
            if gpio_name not in self.config.get('gpio'):
                raise TuxDroidEyesError("Missing `%s` section in `gpio` section "
                                        "in eyes config", gpio_name)
            try:
                int(self.config.get('gpio').get(gpio_name))
            except ValueError:
                raise TuxDroidEyesError("`gpio.%s` should be a integer", gpio_name)

    def _set_callbacks(self):
        """Set button callbacks"""
        for position in ("opened", "closed"):
            sensor = getattr(self, "_{}_sensor".format(position))
            callback = getattr(self, "_{}_event".format(position))
            GPIO.remove_event_detect(sensor)
            GPIO.add_event_detect(sensor,
                                  GPIO.RISING,
                                  callback=callback,
                                  bouncetime=int(BUTTON_BOUNCE_TIME * 1000))

    def _opened_event(self, gpio_id):
        """Opened eyes event callback"""
        # We have to not consider the first event
        if time.time() - self._motor_start_time < 0.2:
            # Maybe we want a debug ?
            self._logger.warning("Startup wings event detected, ignoring it")
            return

        # Check if the gpio_id is correct
        if gpio_id != self._opened_sensor:
            self._logger.error("Bad opened sensor GPIO id")
            raise TuxDroidEyesError("Bad GPIO id when opening")

        self.position = "OPENED"
        self._move_count += 1
        if isinstance(self._wanted_moves, int) and self._move_count >= self._wanted_moves:
            self._wanted_moves = None
            self.stop()
        for callback in self._opened_callbacks:
            self._logger.debug("Calling: %s", callback.__name__)
            self._thread_pool.submit(callback)

    def _closed_event(self, gpio_id):
        """Closed eyes event callback"""
        # We have to not consider the first event
        if time.time() - self._motor_start_time < 0.2:
            # Maybe we want a debug ?
            self._logger.warning("Startup wings event detected, ignoring it")
            return

        # Check if the gpio_id is correct
        if gpio_id != self._closed_sensor:
            self._logger.error("Bad closed sensor GPIO id")
            raise TuxDroidEyesError("Bad GPIO id when closing")

        self.position = "CLOSED"
        self._move_count += 1
        if isinstance(self._wanted_moves, int) and self._move_count >= self._wanted_moves:
            self._wanted_moves = None
            self.stop()
        for callback in self._closed_callbacks:
            self._logger.debug("Calling: %s", callback.__name__)
            self._thread_pool.submit(callback)

    def add_callback(self, position: str, callback):
        """Add callback"""
        if position not in ("closed", "opened"):
            raise TuxDroidEyesError("Bad position, should be 'closed' or 'opened'")
        if not isinstance(callback, types.FunctionType):
            raise TuxDroidEyesError("Callback `%s` is not a function", callback)

        callbacks = getattr(self, "_{}_callbacks".format(position))
        if callback in callbacks:
            self._logger.warning("Callback `%s` already registered to `%s` eyes",
                                 callback.__name__, position)
        else:
            self._logger.info("Adding callback `%s` to `%s` eyes", callback.__name__, position)
            callbacks.add(callback)

    def del_callback(self, position: str, callback):
        """Delete callback"""
        if position not in ("closed", "opened"):
            raise TuxDroidEyesError("Bad position, should be 'closed' or 'opened'")

        callbacks = getattr(self, "_{}_callbacks".format(position))
        if callback not in callbacks:
            self._logger.warning("Callback `%s` not registered to `%s` eyes",
                                 callback.__name__, position)
        else:
            self._logger.info("Deleting callback `%s` to `%s` eyes", callback.__name__, position)
            callbacks.remove(callback)

    def calibrate(self):
        """Moving eyes until it reaches the closed positiion"""
        # Calibration
        self._logger.info("Eyes calibration starting")
        # Init variables
        eyes_nb_moves = 0
        # Start moving
        self.start()
        # Start init
        while eyes_nb_moves < 2:
            # Wait for Rising edge
            GPIO.wait_for_edge(self._opened_sensor, GPIO.RISING)
            eyes_nb_moves += 1
        # Set position
        self.position = "OPENED"
        # Stop moving
        self.stop()
        # Eyes should be closed
        self.is_calibrated = True
        self._logger.info("Eyes calibration done")
        # Set callbacks
        self._set_callbacks()
        # Set it as ready
        self.is_ready = True

    def set_position(self, position):
        """Move eyes to a position"""
        position = position.upper()
        if position not in ["OPENED", "CLOSED"]:
            self._logger.error("Bad eyes position")
            raise TuxDroidEyesError("Bad eyes position")
        # Do nothing if already in position
        if self.position == position:
            self._logger.info("Eyes already in %s position", position)
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
        self._logger.info("close eyes")
        self.set_position("CLOSED")

    def open(self):
        """Move head down"""
        self._logger.info("Open eyes")
        self.set_position("OPENED")

    def move(self, times: int):
        """Move head `n` times

        The count is incremented each time head are in OPENED or CLOSED position
        """
        self._move_count = 0
        self._wanted_moves = times
        # Start moving
        self.start()
        while self.is_moving:
            # Wait for the count
            time.sleep(0.01)
        # Stop moving
        self.stop()
        self._move_count = 0

    def stop(self):
        """Stop moving eyes"""
        self._head.stop("eyes")

    def start(self):
        """Start moving eyes"""
        self._head.start("eyes")
