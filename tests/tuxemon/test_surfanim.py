# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
    def test_init(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        self.assertEqual(animation.loop, True)
        self.assertEqual(animation.state, STOPPED)

    def test_get_frame(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        self.assertEqual(animation.get_frame(0).get_size(), (10, 10))
        self.assertEqual(animation.get_frame(1).get_size(), (20, 20))
        self.assertEqual(animation.get_frame(2).get_size(), (0, 0))
        self.assertEqual(animation.duration, 3.0)

    def test_get_current_frame(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        self.assertEqual(animation.get_current_frame().get_size(), (10, 10))
        animation.update(1.5)
        self.assertEqual(animation.get_current_frame().get_size(), (20, 20))

    def test_is_finished(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames, loop=False)
        self.assertFalse(animation.is_finished())
        animation.play()
        animation.update(3.0)
        self.assertTrue(animation.is_finished())

    def test_play(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        self.assertEqual(animation.state, PLAYING)

    def test_pause(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        animation.pause()
        self.assertEqual(animation.state, PAUSED)

    def test_stop(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        animation.stop()
        self.assertEqual(animation.state, STOPPED)

    def test_update(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        animation.update(1.5)
        self.assertGreaterEqual(animation.elapsed, 1.5 - 0.001)
        self.assertLessEqual(animation.elapsed, 1.5 + 0.001)

    def test_elapsed(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        animation.update(1.5)
        self.assertGreaterEqual(animation.elapsed, 1.5 - 0.001)
        self.assertLessEqual(animation.elapsed, 1.5 + 0.001)
        animation.elapsed = 2.5
        self.assertGreaterEqual(animation.elapsed, 2.5 - 0.001)
        self.assertLessEqual(animation.elapsed, 2.5 + 0.001)

    def test_frames_played(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.play()
        animation.update(1.5)
        self.assertEqual(animation.frames_played, 1)
        animation.frames_played = 0
        self.assertEqual(animation.frames_played, 0)

    def test_rate(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        self.assertEqual(animation.rate, 1.0)
        animation.rate = 2.0
        self.assertEqual(animation.rate, 2.0)

    def test_visibility(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        self.assertTrue(animation.visibility)
        animation.visibility = False
        self.assertFalse(animation.visibility)

    def test_get_rect(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        rect = animation.get_rect()
        self.assertEqual(rect.width, 20)
        self.assertEqual(rect.height, 20)

    def test_flip(self):
        frames = [
            (pygame.Surface((10, 10)), 1.0),
            (pygame.Surface((20, 20)), 2.0),
        ]
        animation = SurfaceAnimation(frames)
        animation.flip("x")
        self.assertEqual(animation.get_frame(0).get_size(), (10, 10))
        self.assertEqual(animation.get_frame(1).get_size(), (20, 20))

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
