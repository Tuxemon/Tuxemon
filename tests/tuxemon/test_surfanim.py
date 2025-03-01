# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest

import pygame

from tuxemon.surfanim import (
    PAUSED,
    PLAYING,
    STOPPED,
    SurfaceAnimation,
    SurfaceAnimationCollection,
    clip,
)


class TestSurfaceAnimation(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        self.animation = SurfaceAnimation(self.frames)

    def tearDown(self):
        pygame.quit()

    def test_init(self):
        self.assertEqual(self.animation.loop, True)
        self.assertEqual(self.animation.state, STOPPED)

    def test_get_frame(self):
        self.assertEqual(self.animation.get_frame(0).get_size(), (10, 10))
        self.assertEqual(self.animation.get_frame(1).get_size(), (20, 20))
        self.assertEqual(self.animation.get_frame(2).get_size(), (0, 0))
        self.assertEqual(self.animation.duration, 3.0)

    def test_get_current_frame(self):
        self.animation.play()
        self.assertEqual(
            self.animation.get_current_frame().get_size(), (10, 10)
        )
        self.animation.update(1.5)
        self.assertEqual(
            self.animation.get_current_frame().get_size(), (20, 20)
        )

    def test_is_finished(self):
        animation = SurfaceAnimation(self.frames, loop=False)
        self.assertFalse(animation.is_finished())
        animation.play()
        animation.update(3.0)
        self.assertTrue(animation.is_finished())

    def test_play(self):
        self.animation.play()
        self.assertEqual(self.animation.state, PLAYING)

    def test_pause(self):
        self.animation.play()
        self.animation.pause()
        self.assertEqual(self.animation.state, PAUSED)

    def test_stop(self):
        self.animation.play()
        self.animation.stop()
        self.assertEqual(self.animation.state, STOPPED)

    def test_update(self):
        self.animation.play()
        self.animation.update(1.5)
        self.assertGreaterEqual(self.animation.elapsed, 1.5 - 0.001)
        self.assertLessEqual(self.animation.elapsed, 1.5 + 0.001)

    def test_elapsed(self):
        self.animation.play()
        self.animation.update(1.5)
        self.assertGreaterEqual(self.animation.elapsed, 1.5 - 0.001)
        self.assertLessEqual(self.animation.elapsed, 1.5 + 0.001)
        self.animation.elapsed = 2.5
        self.assertGreaterEqual(self.animation.elapsed, 2.5 - 0.001)
        self.assertLessEqual(self.animation.elapsed, 2.5 + 0.001)

    def test_frames_played(self):
        self.animation.play()
        self.animation.update(1.5)
        self.assertEqual(self.animation.frames_played, 1)
        self.animation.frames_played = 0
        self.assertEqual(self.animation.frames_played, 0)

    def test_rate(self):
        self.assertEqual(self.animation.rate, 1.0)
        self.animation.rate = 2.0
        self.assertEqual(self.animation.rate, 2.0)

    def test_visibility(self):
        self.assertTrue(self.animation.visibility)
        self.animation.visibility = False
        self.assertFalse(self.animation.visibility)

    def test_get_rect(self):
        rect = self.animation.get_rect()
        self.assertEqual(rect.width, 20)
        self.assertEqual(rect.height, 20)

    def test_flip(self):
        self.animation.flip("x")
        self.assertEqual(self.animation.get_frame(0).get_size(), (10, 10))
        self.assertEqual(self.animation.get_frame(1).get_size(), (20, 20))

    def test_clip(self):
        self.assertEqual(clip(5, 2, 10), 5)
        self.assertEqual(clip(1, 2, 10), 2)
        self.assertEqual(clip(11, 2, 10), 10)


class TestSurfaceAnimationCollection(unittest.TestCase):
    def setUp(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        self.animation = SurfaceAnimation(frames)

    def test_init(self):
        collection = SurfaceAnimationCollection()
        self.assertEqual(collection._animations, [])
        self.assertEqual(collection._state, STOPPED)

    def test_add_single_animation(self):
        collection = SurfaceAnimationCollection(self.animation)
        self.assertEqual(collection._animations, [self.animation])

    def test_add_sequence_of_animations(self):
        animations = [self.animation for _ in range(3)]
        collection = SurfaceAnimationCollection(*animations)
        self.assertEqual(collection._animations, animations)

    def test_add_mapping_of_animations(self):
        animations = {"a": self.animation, "b": self.animation}
        collection = SurfaceAnimationCollection(animations)
        self.assertEqual(collection._animations, list(animations.values()))

    def test_add_multiple_animations(self):
        animations = [self.animation for _ in range(3)]
        collection = SurfaceAnimationCollection()
        collection.add(*animations)
        self.assertEqual(collection._animations, animations)

    def test_play(self):
        collection = SurfaceAnimationCollection(self.animation)
        collection.play()
        self.assertEqual(collection._state, PLAYING)

    def test_pause(self):
        collection = SurfaceAnimationCollection(self.animation)
        collection.pause()
        self.assertEqual(collection._state, PAUSED)

    def test_stop(self):
        collection = SurfaceAnimationCollection(self.animation)
        collection.stop()
        self.assertEqual(collection._state, STOPPED)

    def test_state_property(self):
        collection = SurfaceAnimationCollection(self.animation)
        self.assertEqual(collection.state, STOPPED)

    def test_remove(self):
        animations = [self.animation for _ in range(3)]
        collection = SurfaceAnimationCollection(*animations)
        self.assertEqual(len(collection.animations), 3)
        collection.remove(self.animation)
        self.assertEqual(len(collection.animations), 2)

    def test_clear(self):
        animations = [self.animation for _ in range(3)]
        collection = SurfaceAnimationCollection(*animations)
        self.assertEqual(len(collection.animations), 3)
        collection.clear()
        self.assertEqual(len(collection.animations), 0)
