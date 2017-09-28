"""Module defining TuxDroid Head"""
from concurrent.futures import ThreadPoolExecutor
import logging
import types

from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidHeadError


# Bounce time for rising edge detection: 100ms
BOUNCE_TIME = 0.1
# TODO Improve button bounce time
BUTTON_BOUNCE_TIME = 0.25


class Head():
    """Head Component

    """
    def __init__(self, config: dict):
        # Get logger
        self.logger = logging.getLogger("tuxdroid").getChild("head")
        # static attributes
        self._gpio_names = ('head_button',)
        self._subcomponent_names = ('eyes', 'mouth')
        # TODO validate config
        self.config = config
        self._check_config()
        # Set attributes
        self.is_ready = False
        # Set GPUIO
        GPIO.setmode(GPIO.BCM)
        self.head_button = int(config.get("gpio").get('head_button'))
        GPIO.setup(self.head_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Callbacks
        self._head_callbacks = set()
        # Thread pool
        self.thread_pool = ThreadPoolExecutor()

        # Calibration
        self._set_callbacks()
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

    def _button_detected(self, channel):
        """Callback for all buttons"""
        self.logger.info("Button %s pressed", channel)
        # callbacks
        if channel == self.head_button:
            for callback in self._head_callbacks:
                self.logger.debug("Calling: %s", callback.__name__)
                self.thread_pool.submit(callback)
        else:
            # Should be impossible
            self.logger.error("Bad button")

    def _set_callbacks(self):
        """Set button callbacks"""
        for button in self._gpio_names:
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
            self.logger.warning("Callback `%s` already registered for head", callback.__name__)
        else:
            self.logger.info("Adding callback `%s` for head", callback.__name__)
            self._head_callbacks.add(callback)

    def del_callback(self, callback):
        """Delete callback"""
        if callback not in self._head_callbacks:
            self.logger.warning("Callback `%s` not registered for head", callback.__name__)
        else:
            self.logger.info("Deleting callback `%s` for head", callback.__name__)
            self._head_callbacks.remove(callback)
