"""Module defining TuxDroid robot"""
import logging
import os

import yaml

from tuxdroid.gpio import GPIO, FAKE_GPIO
from tuxdroid.wings import Wings
from tuxdroid.head import Head
from tuxdroid.errors import TuxDroidError


class TuxDroid():
    """TuxDroid main class"""

    def __init__(self, config, logging_level=logging.INFO):
        # Get logger
        self.logging_level = logging_level
        self.logger = None
        self._get_logger()
        # Set GPIO
        GPIO.setmode(GPIO.BCM)

        self._parts = ('wings', 'head')
        # Configuration
        self._config = config
        self._check_config()
        # Handle fake GPIO
        if FAKE_GPIO:
            GPIO.set_config_(self.config)
        # Head
        self.head = Head(self.config['head'])
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

    def _check_config(self):
        """Validate config"""
        if isinstance(self._config, str) and os.path.isfile(self._config):
            with open(self._config) as fhc:
                self.config = yaml.load(fhc)
        elif isinstance(self._config, dict):
            self.config = self._config
        else:
            raise TuxDroidError("`config` argument should be a string (yaml file path) or a dict")
        for part in self._parts:
            if part not in self.config:
                raise TuxDroidError("Part %s is missing from configuration", part)

    def stop(self):
        """Stop all TuxDroid parts"""
        self.wings.stop()
        GPIO.cleanup()
