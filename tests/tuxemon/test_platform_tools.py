# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

from tuxemon.platform.const import events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.platform.tools import keymap, translate_input_event


class TestTranslateInputEvent(unittest.TestCase):
    def test_keymap_match(self):
        event = PlayerInput("button1", "value1", 0.5)
        keymap["button1"] = "mapped_button1"

        result = translate_input_event(event)

        self.assertEqual(result.button, "mapped_button1")
        self.assertEqual(result.value, "value1")
        self.assertEqual(result.hold_time, 0.5)

    def test_keymap_no_match(self):
        event = PlayerInput("button2", "value2", 0.5)

        result = translate_input_event(event)

        self.assertEqual(result, event)

    def test_unicode_match(self):
        event = PlayerInput(events.UNICODE, "n", 0.5)

        result = translate_input_event(event)

        self.assertEqual(result.button, intentions.NOCLIP)
        self.assertEqual(result.value, "n")
        self.assertEqual(result.hold_time, 0.5)

    def test_unicode_no_match(self):
        event = PlayerInput(events.UNICODE, "x", 0.5)

        result = translate_input_event(event)

        self.assertEqual(result, event)

    def test_non_unicode(self):
        event = PlayerInput("button3", "value3", 0.5)

        result = translate_input_event(event)

        self.assertEqual(result, event)
