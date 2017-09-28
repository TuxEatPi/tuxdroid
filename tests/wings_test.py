import time

import pytest

from tuxdroid.wings import Wings
from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidWingsError


class TestWings(object):

    def test_wings_01(self):
        # Defining callbacks
        def left_callback():
            self.left_pressed = True
        def right_callback():
            self.right_pressed = True

        config = {"gpio": {"left_button": 5,
                                     "right_button": 6,
                                     "moving_sensor": 26,
                                     "motor_direction_1": 19,
                                     "motor_direction_2": 13,
                           }
                  }
        GPIO.set_config_({"wings": config})
        wings = Wings(config)
        # Test wigs move
        assert wings.position == "DOWN"
        wings.up()
        assert wings.position == "UP"
        wings.down()
        assert wings.position == "DOWN"
        wings.move(3)
        assert wings.position == "UP"
        wings.up()
        assert wings.position == "UP"
        with pytest.raises(TuxDroidWingsError) as exp:
            wings.set_position("BAD_POSITION")

        # Test callbacks
        self.right_pressed = False
        self.left_pressed = False
        wings.add_callback('left', left_callback)
        assert left_callback in wings._left_callbacks
        wings.add_callback('right', right_callback)
        assert right_callback in wings._right_callbacks
        # Test readd callback
        wings.add_callback('left', left_callback)
        assert left_callback in wings._left_callbacks
        # Test left callbacks
        wings._button_detected(5)
        time.sleep(0.5)
        assert self.left_pressed == True
        wings._button_detected(6)
        time.sleep(0.5)
        assert self.right_pressed == True
        # Test delete callback
        wings.del_callback('left', left_callback)
        assert left_callback not in wings._left_callbacks
        wings.del_callback('right', right_callback)
        assert right_callback not in wings._right_callbacks

        # Bad callbacks
        with pytest.raises(TuxDroidWingsError) as exp:
            wings.add_callback('bad_side', None)
        with pytest.raises(TuxDroidWingsError) as exp:
            wings.add_callback('left', None)
        with pytest.raises(TuxDroidWingsError) as exp:
            wings.del_callback('bad_side', None)
        wings.del_callback('left', left_callback)

        # Bad button
        with pytest.raises(TuxDroidWingsError) as exp:
            wings._button_detected('bad_gpio_id')

        # Bad moves
        with pytest.raises(TuxDroidWingsError) as exp:
            wings._wings_rotation_callback('bad_gpio_id')
        old_position = wings.position
        wings._wings_rotation_callback(wings.moving_sensor)
        assert old_position == wings.position

        wings.is_calibrated = False
        wings.is_moving = True
        wings._wings_rotation_callback(wings.moving_sensor)
        assert old_position == wings.position

        wings.is_calibrated = True
        wings.position = "BAD_POSITION"
        with pytest.raises(TuxDroidWingsError) as exp:
            wings._wings_rotation_callback(wings.moving_sensor)        

        wings.stop()

    def test_tux_badconfig_wings(self):
        config = {'missing_gpio': 5}
        with pytest.raises(TuxDroidWingsError) as exp:
            wings = Wings(config)

        config = {'gpio': {'missing': 4}}
        with pytest.raises(TuxDroidWingsError) as exp:
            wings = Wings(config)

        config = {'gpio': {'left_button': 'badid'}}
        with pytest.raises(TuxDroidWingsError) as exp:
            wings = Wings(config)

