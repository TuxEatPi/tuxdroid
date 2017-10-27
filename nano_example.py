import RPi.GPIO as GPIO
from tuxdroid.tuxdroid import TuxDroid

tux = TuxDroid("config.yaml")

input("Press Enter to stop...")

tux.stop()
