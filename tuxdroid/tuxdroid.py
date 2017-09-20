import asyncio
import logging

import RPi.GPIO as GPIO

from tuxdroid.wings import Wings

class TuxDroid():
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
        self.logger = logging.getLogger("tuxdroid")
        self.logger.setLevel(self.logging_level)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def stop(self):
        self.wings.stop()

    def run(self):
        """Startup function for main loop"""
        asyncio.set_event_loop(self._async_loop)
        self.logger.info("Starting subtasker for %s", self.component.name)
        tasks = [self._send_alive(),
                 self.component.settings.read(watch=True),
                 self.component.settings.read_global(watch=True),
                 # self._wait_for_reload(),
                 ]
        try:
            self._async_loop.run_until_complete(asyncio.wait(tasks))
        except RuntimeError:
            # Do we have to do something ?
            pass
