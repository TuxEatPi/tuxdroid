"""Module defining TuxDroid Wings"""
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import types

from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidWingsError


# Bounce time for rising edge detection: 100ms
BOUNCE_TIME = 0.1
# TODO Improve button bounce time
BUTTON_BOUNCE_TIME = 0.25


class Wings():
    """Wings Component

    .. todo:: Missing wings speed control (using PWM, need to find PWN frequency/duty cycle)
    """
    def __init__(self, config: dict):
        # Get logger
        self._logger = logging.getLogger("tuxdroid").getChild("wings")
        # Set attributes
        self.is_ready = False
        self.is_moving = False
        self.is_calibrated = False
        self.position = None
        # Privates
        self._count = 0
        self._bad_first_detect_on_move = False
        self._gpio_names = ('left_button', 'right_button', 'moving_sensor',
                            'motor_direction_1', 'motor_direction_2')
        # Validate config
        self.config = config
        self._check_config()
        # Set GPUIO
        GPIO.setmode(GPIO.BCM)
        self._left_button = int(config.get("gpio").get('left_button'))
        GPIO.setup(self._left_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._right_button = int(config.get("gpio").get('right_button'))
        GPIO.setup(self._right_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._moving_sensor = int(config.get("gpio").get('moving_sensor'))
        GPIO.setup(self._moving_sensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._motor_direction_1 = int(config.get("gpio").get('motor_direction_1'))
        GPIO.setup(self._motor_direction_1, GPIO.OUT)
        self._motor_direction_2 = int(config.get("gpio").get('motor_direction_2'))
        GPIO.setup(self._motor_direction_2, GPIO.OUT)
        # Callbacks
        self._right_callbacks = set()
        self._left_callbacks = set()
        # Thread pool
        self._thread_pool = ThreadPoolExecutor()
        # Calibration
        self._logger.info("Wings calibration starting")
        self.calibrate()
        self._logger.info("Wings calibration done")
        # Set callbacks
        self._set_callbacks()
        # Set it as ready
        self.is_ready = True

    def _check_config(self):
        """Validate config"""
        if not self.config.get('gpio'):
            raise TuxDroidWingsError("Missing `gpio` section in wings config")
        for gpio_name in self._gpio_names:
            if gpio_name not in self.config.get('gpio'):
                raise TuxDroidWingsError("Missing `%s` section in `gpio` section "
                                         "in wings config", gpio_name)
            try:
                int(self.config.get('gpio').get(gpio_name))
            except ValueError:
                raise TuxDroidWingsError("`gpio.%s` should be a integer", gpio_name)

    def _button_detected(self, gpio_id):
        """Callback for all buttons"""
        self._logger.info("Button %s pressed", gpio_id)
        # callbacks
        if gpio_id == self._right_button:
            for callback in self._right_callbacks:
                self._logger.debug("Calling: %s", callback.__name__)
                self._thread_pool.submit(callback)
        elif gpio_id == self._left_button:
            for callback in self._left_callbacks:
                self._logger.debug("Calling: %s", callback.__name__)
                self._thread_pool.submit(callback)
        else:
            # Should be impossible
            self._logger.error("Bad button")
            raise TuxDroidWingsError("Bad GPIO id when button pressed")

    def _set_callbacks(self):
        """Set button callbacks"""
        for button in ("_left_button", "_right_button"):
            # Remove previous callbak if needed
            GPIO.remove_event_detect(getattr(self, button))
            # Add standard callbacks
            GPIO.add_event_detect(getattr(self, button), GPIO.RISING,
                                  callback=self._button_detected,
                                  bouncetime=int(BUTTON_BOUNCE_TIME * 1000))

    def add_callback(self, side: str, callback):
        """Add callback"""
        if side not in ("left", "right"):
            raise TuxDroidWingsError("Bad side, should be 'left' or 'right'")
        if not isinstance(callback, types.FunctionType):
            raise TuxDroidWingsError("Callback `%s` is not a function", callback)

        callbacks = getattr(self, "_{}_callbacks".format(side))
        if callback in callbacks:
            self._logger.warning("Callback `%s` already registered for `%s` wing",
                                 callback.__name__, side)
        else:
            self._logger.info("Adding callback `%s` for `%s` wing", callback.__name__, side)
            callbacks.add(callback)

    def del_callback(self, side: str, callback):
        """Delete callback"""
        if side not in ("left", "right"):
            raise TuxDroidWingsError("Bad side, should be 'left' or 'right'")

        callbacks = getattr(self, "_{}_callbacks".format(side))
        if callback not in callbacks:
            self._logger.warning("Callback `%s` not registered for `%s` wing",
                                 callback.__name__, side)
        else:
            self._logger.info("Deleting callback `%s` for `%s` wing", callback.__name__, side)
            callbacks.remove(callback)

    def calibrate(self):
        """Moving Wings 3 times and try to put them down

        Wings goes UP more quickly then they goes DOWN
        That's while we time between each detection
        """
        # Init variables
        wings_dectection = None
        last_wings_detection = None
        last_dectection_time = None
        # Movement counter
        wings_nb_moves = 0
        # Start moving
        self.start()
        # Start init
        while wings_nb_moves < 4 or self.position == "UP":
            # Wait for Rising edge
            GPIO.wait_for_edge(self._moving_sensor, GPIO.RISING)
            # Time between each detection
            wings_dectection = time.time()
            # We need at least one another detection
            if last_wings_detection:
                dectection_time = wings_dectection - last_wings_detection
                # Remove too short detections (bad detections)
                if dectection_time > BOUNCE_TIME:
                    # New move detected (UP OR DOWN)
                    wings_nb_moves += 1
                    if last_dectection_time is None:
                        # First Move detected
                        last_dectection_time = dectection_time
                    elif last_dectection_time > dectection_time:
                        # Position UP detected
                        self.position = "UP"
                    else:
                        # Position DOWN detected
                        self.position = "DOWN"
                    last_dectection_time = dectection_time
            last_wings_detection = wings_dectection
        # Stop moving
        self.stop()
        # Wings should be down
        self.is_calibrated = True
        # Set callback for wings move detection
        GPIO.remove_event_detect(self._moving_sensor)
        GPIO.add_event_detect(self._moving_sensor, GPIO.RISING,
                              callback=self._wings_rotation_callback,
                              bouncetime=int(BOUNCE_TIME * 1000))

    def _wings_rotation_callback(self, gpio_id):
        """Callback method detecting wings movement

        The method is called each time wings are up or down
        """
        # Check if the gpio_id is correct
        if gpio_id != self._moving_sensor:
            self._logger.error("Bad moving sensor GPIO id")
            raise TuxDroidWingsError("Bad GPIO id when moving")
        # We have to not consider the first event
        if self._bad_first_detect_on_move:
            self._bad_first_detect_on_move = False
            return
        # Check if the wings are moving
        if not self.is_moving:
            self._logger.error("Wings are not moving")
            return
        # Check if the wings are calibrated
        if not self.is_calibrated:
            self._logger.error("Wings are not calibrated")
            return
        self._logger.debug("Moving detection - Current position: %s", self.position)
        if self.position == "UP":
            self.position = "DOWN"
            self._count += 1
            self._logger.info("Position DOWN")
        elif self.position == "DOWN":
            self.position = "UP"
            self._count += 1
            self._logger.info("Position UP")
        else:
            raise TuxDroidWingsError("Bad position")

    def start(self):
        """Start moving wings"""
        if not self.is_moving:
            self._bad_first_detect_on_move = True
            self._logger.info("Starting moving wings")
            GPIO.output(self._motor_direction_1, GPIO.HIGH)
            self.is_moving = True

    def set_position(self, position):
        """Move wings to a position"""
        position = position.upper()
        if position not in ["UP", "DOWN"]:
            self._logger.error("Bad wings position")
            raise TuxDroidWingsError("Bad position")
        # Do nothing if already in position
        if self.position == position:
            self._logger.info("Wings already in %s position", position)
            return
        # Start moving
        self.start()
        # Wait for position
        # TODO add timeout
        while self.position != position:
            pass
        # Stop moving
        self.stop()

    def up(self):  # pylint: disable=C0103
        """Move wings up"""
        self._logger.info("Move wings up")
        self.set_position("UP")

    def down(self):
        """Move wings down"""
        self._logger.info("Move wings down")
        self.set_position("DOWN")

    def move(self, times):
        """Move wings `n` times

        The count is incremented each time wings are in UP or DOWN position
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
        """Stop moving wings"""
        if self.is_moving:
            self._logger.info("Stop wings")
            self.is_moving = False
            GPIO.output(self._motor_direction_1, GPIO.LOW)
            GPIO.output(self._motor_direction_2, GPIO.HIGH)
            time.sleep(0.02)
            GPIO.output(self._motor_direction_2, GPIO.LOW)
