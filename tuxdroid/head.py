"""Module defining TuxDroid Head"""
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import types

from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidHeadError
from tuxdroid.mouth import Mouth


# TODO Improve button bounce time
BUTTON_BOUNCE_TIME = 0.25


class Head():
    """Head Component

    """
    def __init__(self, config: dict):
        # Get logger
        self._logger = logging.getLogger("tuxdroid").getChild("head")
        # Set attributes
        self.is_ready = False
        # Privates
        self._gpio_names = ('head_button',)
        self._subcomponent_names = ('eyes', 'mouth')
        # TODO validate config
        self.config = config
        self._check_config()
        # Set GPUIO
        GPIO.setmode(GPIO.BCM)
        self._head_button = int(config.get("gpio").get('head_button'))
        GPIO.setup(self._head_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Thread pool
        self._thread_pool = ThreadPoolExecutor()
        # Set callbacks
        self._head_callbacks = set()
        self._set_callbacks()

        # Init subcomponent
        self.mouth = Mouth(self, config.get('mouth'))
        self._motor_mouth = int(config.get("mouth").get("gpio").get('motor'))
        GPIO.setup(self._motor_mouth, GPIO.OUT)
        self._motor_eyes = int(config.get("eyes").get("gpio").get('motor'))
        GPIO.setup(self._motor_eyes, GPIO.OUT)
        # Calibration
        self.mouth.calibrate()
        # Set it as ready
        self.is_ready = True

    def _check_config(self):
        """Validate config"""
        if not self.config.get('gpio'):
            raise TuxDroidHeadError("Missing `gpio` section in head config")
        for gpio_name in self._gpio_names:
            if gpio_name not in self.config.get('gpio'):
                raise TuxDroidHeadError("Missing `%s` section in `gpio` section "
                                        "in head config", gpio_name)
            try:
                int(self.config.get('gpio').get(gpio_name))
            except ValueError:
                raise TuxDroidHeadError("`gpio.%s` should be a integer", gpio_name)
        for subcomponent in self._subcomponent_names:
            if subcomponent not in self.config:
                raise TuxDroidHeadError("Missing `%s` section in head config",
                                        subcomponent)

    def _button_detected(self, gpio_id):
        """Callback for all buttons"""
        self._logger.info("Button %s pressed", gpio_id)
        # callbacks
        if gpio_id == self._head_button:
            for callback in self._head_callbacks:
                self._logger.debug("Calling: %s", callback.__name__)
                self._thread_pool.submit(callback)
        else:
            # Should be impossible
            self._logger.error("Bad button")
            raise TuxDroidHeadError("Bad GPIO id when button pressed")

    def _set_callbacks(self):
        """Set button callbacks"""
        for button in self._gpio_names:
            button = "_{}".format(button)
            # Remove previous callbak if needed
            GPIO.remove_event_detect(getattr(self, button))
            # Add standard callbacks
            GPIO.add_event_detect(getattr(self, button), GPIO.RISING,
                                  callback=self._button_detected,
                                  bouncetime=int(BUTTON_BOUNCE_TIME * 1000))

    def add_callback(self, callback):
        """Add callback"""
        if not isinstance(callback, types.FunctionType):
            raise TuxDroidHeadError("Callback `%s` is not a function", callback)

        if callback in self._head_callbacks:
            self._logger.warning("Callback `%s` already registered to head", callback.__name__)
        else:
            self._logger.info("Adding callback `%s` to head", callback.__name__)
            self._head_callbacks.add(callback)

    def del_callback(self, callback):
        """Delete callback"""
        if callback not in self._head_callbacks:
            self._logger.warning("Callback `%s` not registered to head", callback.__name__)
        else:
            self._logger.info("Deleting callback `%s`to head", callback.__name__)
            self._head_callbacks.remove(callback)

    def start(self, component):
        """Start moving eyes or mouth"""
        if component not in ("eyes", "mouth"):
            raise TuxDroidHeadError("Component should be `eyes` or `mouth`")
        # TODO: handle
        # * mouth can NOT move when eyes are moving
        # * eyes can NOT move when mouth is moving



        elif component == "mouth":
            if not self.mouth.is_moving:
                # Remove the startup moving event
                # So we don't need remove the first bad detection
                self.mouth._motor_start_time = time.time()
                # Reset movement count
                self.mouth._count = 0
                # Starting moving
                self.mouth._logger.info("Starting moving mouth")
                GPIO.output(self._motor_eyes, GPIO.LOW)
                GPIO.output(self._motor_mouth, GPIO.HIGH)
                self.mouth.is_moving = True
#        elif component == "eyes":
#            if not self.eyes.is_moving:
#                # Remove the startup moving event
#                # So we don't need remove the first bad detection
#                self.eyes._motor_start_time = time.time()
#                # Reset movement count
#                self.eyes._count = 0
#                # Starting moving
#                self.eyes._logger.info("Starting moving eyes")
#                GPIO.output(self._motor_mouth, GPIO.LOW)
#                GPIO.output(self._motor_eyes, GPIO.HIGH)
#                self.eyes.is_moving = True

    def stop(self, component=None):
        """Stop moving eyes and mouth"""
        if component is None:
            self._logger.info("Stopping mouth and eyes")
        elif not hasattr(self, component):
            raise TuxDroidHeadError("Component should be `eyes` or `mouth`")
        else:
            getattr(self, component)._logger.info("Stopping {}".format(component))
        GPIO.output(self._motor_mouth, GPIO.LOW)
        GPIO.output(self._motor_eyes, GPIO.LOW)
        self.mouth.is_moving = False
#        self.eyes.is_moving = False
