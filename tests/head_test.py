import time

import pytest

from tuxdroid.head import Head
from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidHeadError, TuxDroidMouthError


class TestTux(object):

    def test_head_01(self):

        # Defining callbacks
        self.head_pressed = False
        def head_callback():
            self.head_pressed = True
        self.mouth_opened = False
        def mouth_opened_callback():
            self.mouth_opened = True
        self.mouth_closed = False
        def mouth_closed_callback():
            self.mouth_closed = True


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
        head.add_callback(head_callback)
        assert head_callback in head._head_callbacks
        head._button_detected(12)
        assert self.head_pressed == True
        head.add_callback(head_callback)
        assert head_callback in head._head_callbacks
        head.del_callback(head_callback)
        assert head_callback not in head._head_callbacks
        head.del_callback(head_callback)
        assert head_callback not in head._head_callbacks
        # Bad callbacks
        with pytest.raises(TuxDroidHeadError) as exp:
            head.add_callback('bad_callback')
        # Bad button
        with pytest.raises(TuxDroidHeadError) as exp:
            head._button_detected('bag_gpio')

        # Mouth
        assert head.mouth.position == "CLOSED"
        head.mouth.open()
        head.mouth.open()
        assert head.mouth.position == "OPENED"
        head.mouth.close()
        assert head.mouth.position == "CLOSED"
        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth.set_position("BAD_POSITION")

        head.mouth.add_callback("closed", mouth_closed_callback)
        assert mouth_closed_callback in head.mouth._closed_callbacks
        head.mouth.add_callback("opened", mouth_opened_callback)
        assert mouth_opened_callback in head.mouth._opened_callbacks
        head.mouth.add_callback("opened", mouth_opened_callback)
        assert mouth_opened_callback in head.mouth._opened_callbacks

        head.mouth._opened_event(21)
        assert self.mouth_opened == True
        head.mouth._closed_event(20)
        assert self.mouth_closed == True

        head.mouth.del_callback("opened", mouth_opened_callback)
        assert mouth_opened_callback not in head.mouth._opened_callbacks

#        head.mouth.move(1)
#        assert head.mouth.position == "OPENED"

    def test_tux_badconfig_head(self):
        config = {}
        with pytest.raises(TuxDroidHeadError) as exp:
            head = Head(config)

        config = {"gpio": {'missing': 5}}
        with pytest.raises(TuxDroidHeadError) as exp:
            head = Head(config)

        config = { "gpio": {'head_button': 'badid'}}
        with pytest.raises(TuxDroidHeadError) as exp:
            head = Head(config)

        config = { "gpio": {'head_button': 12}}
        with pytest.raises(TuxDroidHeadError) as exp:
            head = Head(config)
