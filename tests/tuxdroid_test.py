import time

import pytest

from tuxdroid.tuxdroid import TuxDroid
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
        # Test wigs move
        assert tux.wings.position == "DOWN"
        tux.wings.up()
        assert tux.wings.position == "UP"
        tux.wings.down()
        assert tux.wings.position == "DOWN"
        tux.wings.move(3)
        assert tux.wings.position == "UP"
        tux.wings.up()
        assert tux.wings.position == "UP"
        with pytest.raises(TuxDroidWingsError) as exp:
            tux.wings.set_position("BAD_POSITION")

        # Test callbacks
        self.right_pressed = False
        self.left_pressed = False
        tux.wings.add_callback('left', left_callback)
        assert left_callback in tux.wings._left_callbacks
        tux.wings.add_callback('right', right_callback)
        assert right_callback in tux.wings._right_callbacks
        # Test readd callback
        tux.wings.add_callback('left', left_callback)
        assert left_callback in tux.wings._left_callbacks
        # Test left callbacks
        tux.wings._button_detected(5)
        time.sleep(0.5)
        assert self.left_pressed == True
        tux.wings._button_detected(6)
        time.sleep(0.5)
        assert self.right_pressed == True
        # Test delete callback
        tux.wings.del_callback('left', left_callback)
        assert left_callback not in tux.wings._left_callbacks
        tux.wings.del_callback('right', right_callback)
        assert right_callback not in tux.wings._right_callbacks

        tux.stop()

    def test_tux_02(self):
        # Defining callbacks
        def left_callback():
            self.left_pressed = True

        config_file = "tests/tuxdroid_test_config.yaml"
        tux = TuxDroid(config_file)
        assert tux.wings.position == "DOWN"
        with pytest.raises(TuxDroidWingsError) as exp:
            tux.wings.add_callback('bad_side', None)
        with pytest.raises(TuxDroidWingsError) as exp:
            tux.wings.add_callback('left', None)
        with pytest.raises(TuxDroidWingsError) as exp:
            tux.wings.del_callback('bad_side', None)
        tux.wings.del_callback('left', left_callback)
        tux.stop()

    def test_tux_badconfig_01(self):
        config = None
        with pytest.raises(TuxDroidError) as exp:
            tux = TuxDroid(config)

    def test_tux_badconfig_02(self):
        config = {}
        with pytest.raises(TuxDroidError) as exp:
            tux = TuxDroid(config)

    def test_tux_badconfig_03(self):
        config = {'wings': {}, "head": {}}
        with pytest.raises(TuxDroidError) as exp:
            tux = TuxDroid(config)

    def test_tux_badconfig_04(self):
        config = {'wings': {'gpio': {'missing': 4}},
                  "head": {"gpio": {'missing': 5}}}
        with pytest.raises(TuxDroidHeadError) as exp:
            tux = TuxDroid(config)

    def test_tux_badconfig_05(self):
        config = {'wings': {'gpio': {'left_button': 'badid'}},
                  "head": { "gpio": {'head_button': 'badid'}}}
        with pytest.raises(TuxDroidHeadError) as exp:
            tux = TuxDroid(config)
