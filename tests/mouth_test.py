import time
from unittest.mock import MagicMock

import pytest

from tuxdroid.head import Head
from tuxdroid.mouth import Mouth
from tuxdroid.gpio import GPIO
from tuxdroid.errors import TuxDroidMouthError


class TestTuxMouth(object):

    def test_mouth_01(self):
        # Defining callbacks
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

        assert head.mouth.position == "CLOSED"
        head.mouth.open()
        head.mouth.open()
        assert head.mouth.position == "OPENED"
        head.mouth.close()
        assert head.mouth.position == "CLOSED"
        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth.set_position("BAD_POSITION")

        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth.add_callback("bad_position", mouth_closed_callback)
        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth.add_callback("opened", "bad_callback")

        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth.del_callback("bad_position", mouth_closed_callback)

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
        head.mouth.del_callback("opened", mouth_opened_callback)
        assert head.mouth._opened_callbacks == set()

        head.mouth.move(1)
        assert head.mouth.position == "OPENED"
        head.mouth.move(1)
        assert head.mouth.position == "CLOSED"

        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth._opened_event('bad_gpio_id')

        with pytest.raises(TuxDroidMouthError) as exp:
            head.mouth._closed_event('bad_gpio_id')

    def test_tux_mouth_02(self):
        config = {}
        fake_head = MagicMock()
        with pytest.raises(TuxDroidMouthError) as exp:
            mouth = Mouth(fake_head, config)

        config = {"gpio": {'missing': 5}}
        with pytest.raises(TuxDroidMouthError) as exp:
            mouth = Mouth(fake_head, config)

        config = {"gpio": {'motor': 'badid',
                           'opened_sensor': 1,
                           'closed_sensor': 2,
                           }}
        with pytest.raises(TuxDroidMouthError) as exp:
            mouth = Mouth(fake_head, config)
