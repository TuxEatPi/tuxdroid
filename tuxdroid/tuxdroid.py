"""Module defining TuxDroid robot"""
import logging

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    from tuxdroid import fake_gpui as GPIO

from tuxdroid.wings import Wings


class TuxDroid():
    """TuxDroid main class"""

    def __init__(self, config, logging_level=logging.INFO):
        # Get logger
        self.logging_level = logging_level
        self.logger = None
        self._get_logger()
        # Set GPIO
        GPIO.setmode(GPIO.BCM)

        # GPIO
        self.config = config
        # Wings
        self.wings = Wings(self.config['wings'])

    def _get_logger(self):
        """Get logger"""
        self.logger = logging.getLogger("tuxdroid")
        self.logger.setLevel(self.logging_level)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def stop(self):
        """Stop all TuxDroid parts"""
        self.wings.stop()
