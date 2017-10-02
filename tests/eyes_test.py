import time
from unittest.mock import MagicMock

import pytest

from tuxdroid.head import Head
from tuxdroid.eyes import Eyes
from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidEyesError


class TestTuxEyes(object):

    def test_eyes_01(self):
        # Defining callbacks
        self.eyes_opened = False
        def eyes_opened_callback():
            self.eyes_opened = True
        self.eyes_closed = False
        def eyes_closed_callback():
            self.eyes_closed = True

        config = {"gpio": {"head_button": 12},
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
                  }
        GPIO.set_config_({"head": config})
        head = Head(config)

        assert head.eyes.position == "OPENED"
        head.eyes.open()
        assert head.eyes.position == "OPENED"
        head.eyes.close()
        assert head.eyes.position == "CLOSED"
        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes.set_position("BAD_POSITION")

        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes.add_callback("bad_position", eyes_closed_callback)
        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes.add_callback("opened", "bad_callback")

        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes.del_callback("bad_position", eyes_closed_callback)

        head.eyes.add_callback("closed", eyes_closed_callback)
        assert eyes_closed_callback in head.eyes._closed_callbacks
        head.eyes.add_callback("opened", eyes_opened_callback)
        assert eyes_opened_callback in head.eyes._opened_callbacks
        head.eyes.add_callback("opened", eyes_opened_callback)
        assert eyes_opened_callback in head.eyes._opened_callbacks

        head.eyes._opened_event(7)
        assert self.eyes_opened == True
        head.eyes._closed_event(8)
        assert self.eyes_closed == True

        head.eyes.del_callback("opened", eyes_opened_callback)
        assert eyes_opened_callback not in head.eyes._opened_callbacks
        head.eyes.del_callback("opened", eyes_opened_callback)
        assert head.eyes._opened_callbacks == set()

        head.eyes.move(1)
        assert head.eyes.position == "OPENED"
        head.eyes.move(1)
        assert head.eyes.position == "CLOSED"

        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes._opened_event('bad_gpio_id')

        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes._closed_event('bad_gpio_id')

        # Led
        head.eyes.led_on()
        assert head.eyes.led_right == True
        assert head.eyes.led_left == True
        head.eyes.led_off()
        assert head.eyes.led_right == False
        assert head.eyes.led_left == False
        head.eyes.led_on('right')
        assert head.eyes.led_right == True
        assert head.eyes.led_left == False
        head.eyes.led_off('right')
        assert head.eyes.led_right == False
        assert head.eyes.led_left == False

        head.eyes.led_blink(2)
        assert head.eyes.led_right == False
        assert head.eyes.led_left == False

        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes.led_off('bad_side')
        with pytest.raises(TuxDroidEyesError) as exp:
            head.eyes.led_on('bad_side')

    def test_tux_eyes_02(self):
        config = {}
        fake_head = MagicMock()
        with pytest.raises(TuxDroidEyesError) as exp:
            Eyes(fake_head, config)

        config = {"gpio": {'missing': 5}}
        with pytest.raises(TuxDroidEyesError) as exp:
            Eyes(fake_head, config)

        config = {"gpio": {'motor': 'badid',
                           'opened_sensor': 1,
                           'closed_sensor': 2,
                           }}
        with pytest.raises(TuxDroidEyesError) as exp:
            Eyes(fake_head, config)
