import time

import pytest

from tuxdroid.tuxdroid import TuxDroid
from tuxdroid.wings import Wings
from tuxdroid.wings import Wings
from tuxdroid.errors import TuxDroidError, TuxDroidWingsError, TuxDroidHeadError


class TestTux(object):

    def test_tux_01(self):

        # Defining callbacks
        def left_callback():
            self.left_pressed = True
        def right_callback():
            self.right_pressed = True

        config = {"wings": {"gpio": {"left_button": 5,
                                     "right_button": 6,
                                     "moving_sensor": 26,
                                     "motor_direction_1": 19,
                                     "motor_direction_2": 13,
                                     }
                            },
                  "head": {"gpio": {"head_button": 12},
                           "mouth": {"gpio": {"opened_sensor": 21,
                                              "closed_sensor": 20,
                                              "motor": 16,
                                              },
                                    },
                           "eyes": {"gpio": {"opened_sensor": 7,
                                             "closed_sensor": 8,
                                             "motor": 25,
                                             "left_led": 23,
                                             "right_led": 24,
                                              },
                                    },
                           },
                  }
        tux = TuxDroid(config)
        assert tux.wings.position == "DOWN"

        tux.stop()

    def test_tux_02(self):
        config_file = "tests/tuxdroid_test_config.yaml"
        tux = TuxDroid(config_file)
        assert tux.wings.position == "DOWN"
        tux.stop()

    def test_tux_badconfig_01(self):
        config = None
        with pytest.raises(TuxDroidError) as exp:
            tux = TuxDroid(config)

    def test_tux_badconfig_02(self):
        config = {}
        with pytest.raises(TuxDroidError) as exp:
            tux = TuxDroid(config)

    def test_tux_badconfig_head(self):
#        config = {'wings': {}, "head": {}}
#        with pytest.raises(TuxDroidError) as exp:
 #           tux = TuxDroid(config)

        config = {'wings': {'gpio': {'missing': 4}},
                  "head": {"gpio": {'missing': 5}}}
        with pytest.raises(TuxDroidHeadError) as exp:
            tux = TuxDroid(config)

        config = {'wings': {'gpio': {'left_button': 'badid'}},
                  "head": { "gpio": {'head_button': 'badid'}}}
        with pytest.raises(TuxDroidHeadError) as exp:
            tux = TuxDroid(config)
