"""Module for faking GPIO library"""
# pylint: disable=C0103
from unittest.mock import MagicMock

setmode = MagicMock()

BCM = None
