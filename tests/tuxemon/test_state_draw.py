# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

import pygame

from tuxemon import prepare
from tuxemon.state.draw import EventDebugDrawer, Renderer, StateDrawer


class TestRenderer(unittest.TestCase):

    def setUp(self):
        self.debug_drawer = MagicMock()
        self.screen = MagicMock()
        self.state_drawer = MagicMock()
        self.config = MagicMock()
        self.config.window_caption = "Test Caption"
        self.config.vsync = False
        self.renderer = Renderer(
            self.screen, self.state_drawer, self.config, self.debug_drawer
        )

    def test_init(self):
        self.assertEqual(self.renderer.screen, self.screen)
        self.assertEqual(self.renderer.state_drawer, self.state_drawer)
        self.assertEqual(self.renderer.caption, self.config.window_caption)
        self.assertEqual(self.renderer.frames, 0)
        self.assertEqual(self.renderer.fps_timer, 0.0)

    def test_draw(self):
        self.renderer.draw()
        self.state_drawer.draw.assert_called_once()

    def test_draw_debug(self):
        partial_events = [MagicMock()]
        self.renderer.draw_debug(partial_events)
        self.debug_drawer.draw_event_debug.assert_called_once_with(
            partial_events
        )

    @patch("pygame.image.save")
    def test_save_frame(self, mock_save):
        frame_number = 42
        self.renderer.save_frame(frame_number)
        mock_save.assert_called_once_with(self.screen, "snapshot00042.tga")

    def test_update(self):
        self.renderer.frames = 59
        self.renderer.fps_timer = 1.0
        self.renderer.update(0.0)
        self.assertEqual(self.renderer.frames, 0)
        self.assertEqual(self.renderer.fps_timer, 0.0)

    def test_update_accumulates_and_resets(self):
        # Simulate 61 frames at ~0.0165s each = ~1.0065s
        for _ in range(61):
            self.renderer.update(0.0165)

        self.assertEqual(self.renderer.frames, 0)
        self.assertEqual(self.renderer.fps_timer, 0.0)

    def test_update_accumulates_without_reset(self):
        for _ in range(60):
            self.renderer.update(0.016)

        self.assertEqual(self.renderer.frames, 60)
        self.assertAlmostEqual(self.renderer.fps_timer, 0.96, places=2)

    @patch("pygame.display.set_caption")
    def test_update_sets_caption_with_vsync(self, mock_set_caption):
        self.config.vsync = True
        self.renderer.vsync = True
        self.renderer.frames = 60
        self.renderer.fps_timer = 1.0
        self.renderer.update(0.0)
        mock_set_caption.assert_called_once()
        args = mock_set_caption.call_args[0][0]
        self.assertIn("VSync ON", args)

    @patch("pygame.display.set_caption")
    def test_update_sets_caption_without_vsync(self, mock_set_caption):
        self.config.vsync = False
        self.renderer.vsync = False
        self.renderer.frames = 60
        self.renderer.fps_timer = 1.0
        self.renderer.update(0.0)
        mock_set_caption.assert_called_once()
        args = mock_set_caption.call_args[0][0]
        self.assertIn("VSync OFF", args)

    @patch("pygame.image.save")
    def test_save_frame_filename_format(self, mock_save):
        self.renderer.save_frame(7)
        mock_save.assert_called_once_with(self.screen, "snapshot00007.tga")

    def test_draw_debug_with_empty_events(self):
        self.renderer.draw_debug([])
        self.debug_drawer.draw_event_debug.assert_called_once_with([])


class TestStateDrawer(unittest.TestCase):

    def setUp(self):
        self.surface = MagicMock()
        self.state_manager = MagicMock()
        self.config = MagicMock()
        self.state_drawer = StateDrawer(
            self.surface, self.state_manager, self.config
        )
        self.state1 = MagicMock()
        self.state2 = MagicMock()

    def test_init(self):
        self.assertEqual(self.state_drawer.surface, self.surface)
        self.assertEqual(self.state_drawer.state_manager, self.state_manager)
        self.assertEqual(self.state_drawer.config, self.config)

    def test_draw(self):
        self.state_manager.active_states = [self.state1, self.state2]
        self.state_drawer.draw()
        self.state1.draw.assert_called_once_with(self.surface)
        self.state2.draw.assert_called_once_with(self.surface)

    def test_draw_with_transparency(self):
        self.state1.transparent = False
        self.state1.rect = MagicMock()
        self.state1.rect.return_value = (0, 0, 100, 100)
        self.state_manager.active_states = [self.state1, self.state2]
        self.state_drawer.draw()
        self.state1.draw.assert_called_once_with(self.surface)
        self.state2.draw.assert_called_once_with(self.surface)

    def test_draw_with_full_screen(self):
        self.state1.transparent = False
        self.state1.rect = MagicMock()
        self.state1.rect.return_value = (0, 0, 100, 100)
        self.state1.force_draw = False
        self.state_manager.active_states = [self.state1, self.state2]
        self.surface.get_rect.return_value = (0, 0, 100, 100)
        self.state1.rect.return_value = (0, 0, 100, 100)
        self.state_drawer.draw()
        self.state1.draw.assert_called_once_with(self.surface)
        self.state2.draw.assert_called_once_with(self.surface)


class TestEventDebugDrawer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_init(self):
        screen = MagicMock()
        event_debug_drawer = EventDebugDrawer(screen)
        self.assertEqual(event_debug_drawer.screen, screen)
        self.assertEqual(event_debug_drawer.max_width, 1000)
        self.assertEqual(event_debug_drawer.x_offset, 20)
        self.assertEqual(event_debug_drawer.y_offset, 200)
        self.assertEqual(event_debug_drawer.initial_x, 4)
        self.assertEqual(event_debug_drawer.initial_y, 20)
        self.assertEqual(event_debug_drawer.success_color, prepare.GREEN_COLOR)
        self.assertEqual(event_debug_drawer.failure_color, prepare.RED_COLOR)

    def test_draw_event_debug(self):
        screen = MagicMock()
        event_debug_drawer = EventDebugDrawer(screen)
        event1 = [(True, MagicMock()), (False, MagicMock())]
        event1[0][1].parameters = ["param1", "param2"]
        event1[1][1].parameters = ["param3", "param4"]
        event2 = [(True, MagicMock()), (False, MagicMock())]
        event2[0][1].parameters = ["param5", "param6"]
        event2[1][1].parameters = ["param7", "param8"]
        event_debug_drawer.draw_event_debug([event1, event2])
        self.assertTrue(screen.blit.called)

    def test_render_text(self):
        screen = MagicMock()
        event_debug_drawer = EventDebugDrawer(screen)
        text = "Test text"
        color = (255, 0, 0)
        position = (10, 20)
        font_size = 15
        event_debug_drawer.render_text(text, color, position, font_size)
        self.assertTrue(screen.blit.called)
