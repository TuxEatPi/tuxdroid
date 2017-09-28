import time

import pytest

from tuxdroid.tuxdroid import TuxDroid
from tuxdroid.head import Head
from tuxdroid.errors import TuxDroidHeadError


class TestTux(object):

    def test_head_01(self):

        # Defining callbacks
        self.head_pressed = False
        def head_callback():
            self.head_pressed = True

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
