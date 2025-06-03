# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

import pygame

from tuxemon import prepare
from tuxemon.state_draw import EventDebugDrawer, Renderer, StateDrawer


class TestRenderer(unittest.TestCase):

    def setUp(self):
        self.debug_drawer = MagicMock()
        self.screen = MagicMock()
        self.state_drawer = MagicMock()
        self.config = MagicMock()
        self.config.window_caption = "Test Caption"
        self.renderer = Renderer(self.screen, self.state_drawer, self.config)

    def test_init(self):
        self.assertEqual(self.renderer.screen, self.screen)
        self.assertEqual(self.renderer.state_drawer, self.state_drawer)
        self.assertEqual(self.renderer.caption, self.config.window_caption)
        self.assertEqual(self.renderer.frames, 0)
        self.assertEqual(self.renderer.fps_timer, 0.0)

    @patch("pygame.image.save")
    def test_draw_save_to_disk(self, mock_save):
        frame_number = 1
        save_to_disk = True
        collision_map = False
        partial_events = []
        self.renderer.draw(
            frame_number,
            save_to_disk,
            collision_map,
            self.debug_drawer,
            partial_events,
        )
        self.state_drawer.draw.assert_called_once()
        mock_save.assert_called_once_with(self.screen, "snapshot00001.tga")

    @patch("pygame.image.save")
    def test_draw_dont_save_to_disk(self, mock_save):
        frame_number = 1
        save_to_disk = False
        collision_map = False
        partial_events = []
        self.renderer.draw(
            frame_number,
            save_to_disk,
            collision_map,
            self.debug_drawer,
            partial_events,
        )
        self.state_drawer.draw.assert_called_once()
        mock_save.assert_not_called()

    @patch("pygame.image.save")
    def test_draw_collision_map(self, mock_save):
        frame_number = 1
        save_to_disk = False
        collision_map = True
        partial_events = []
        self.renderer.draw(
            frame_number,
            save_to_disk,
            collision_map,
            self.debug_drawer,
            partial_events,
        )
        self.state_drawer.draw.assert_called_once()
        self.debug_drawer.draw_event_debug.assert_called_once_with(
            partial_events
        )

    @patch("pygame.image.save")
    def test_draw_no_collision_map(self, mock_save):
        frame_number = 1
        save_to_disk = False
        collision_map = False
        partial_events = []
        self.renderer.draw(
            frame_number,
            save_to_disk,
            collision_map,
            self.debug_drawer,
            partial_events,
        )
        self.state_drawer.draw.assert_called_once()
        self.debug_drawer.draw_event_debug.assert_not_called()


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
