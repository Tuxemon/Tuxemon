# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.animation import Animation, AnimationState


class TestAnimation(unittest.TestCase):
    def setUp(self) -> None:
        self.ani = Animation(x=100, y=100, duration=1000)
        self.sprite = MagicMock()

    def test_init(self):
        self.assertEqual(self.ani.props, {"x": 100, "y": 100})
        self.assertEqual(self.ani.delay, 0)
        self.assertEqual(self.ani._duration, 1000)
        self.assertEqual(self.ani._relative, False)

    def test_start(self):
        self.ani.start(self.sprite)
        self.assertEqual(self.ani._state, AnimationState.RUNNING)
        self.assertEqual(self.ani._targets, (self.sprite,))

    def test_update(self):
        self.ani.start(self.sprite)
        self.ani.update(500)
        self.assertEqual(self.ani._elapsed, 500)

    def test_finish(self):
        self.ani.start(self.sprite)
        self.ani.finish()
        self.assertEqual(self.ani._state, AnimationState.FINISHED)

    def test_abort(self):
        self.ani.start(self.sprite)
        self.ani.abort()
        self.assertEqual(self.ani._state, AnimationState.FINISHED)

    def test_get_value(self):
        self.sprite.x = 50
        self.assertEqual(self.ani._get_value(self.sprite, "x"), 50)

    def test_set_value(self):
        self.ani._set_value(self.sprite, "x", 100)
        self.sprite.x.assert_called_once_with(100)

    def test_callback(self):
        callback = MagicMock()
        self.ani.callback = callback
        self.ani.start(MagicMock())
        self.ani.finish()
        callback.assert_called_once()

    def test_update_callback(self):
        update_callback = MagicMock()
        self.ani.update_callback = update_callback
        self.ani.start(MagicMock())
        self.ani.update(1000)
        self.assertGreater(update_callback.call_count, 0)
