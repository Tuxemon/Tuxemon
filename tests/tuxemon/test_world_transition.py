# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest import TestCase
from unittest.mock import MagicMock, patch

from tuxemon.states.world.world_transition import WorldTransition


class TestTransition(TestCase):
    def setUp(self):
        self.mock_world = MagicMock()
        self.mock_world.client.screen.get_size.return_value = (800, 600)
        self.mock_world.player = MagicMock()

        self.transition = WorldTransition(self.mock_world)

    def test_transition_initialization(self):
        self.assertIsNone(self.transition.transition_surface)
        self.assertEqual(self.transition.transition_alpha, 0)
        self.assertFalse(self.transition.in_transition)

    def test_set_transition_surface_size(self):
        color = (0, 0, 0, 255)
        self.transition.set_transition_surface(color)

        self.assertEqual(
            self.transition.transition_surface.get_size(), (800, 600)
        )

    def test_draw_no_action(self):
        mock_surface = MagicMock()

        self.transition.set_transition_state(False)
        self.transition.draw(mock_surface)

        mock_surface.blit.assert_not_called()

    def test_transition_state_changes(self):
        self.transition.set_transition_state(True)
        self.assertTrue(self.transition.in_transition)

        self.transition.set_transition_state(False)
        self.assertFalse(self.transition.in_transition)

    def test_set_transition_surface(self):
        mock_color = (255, 0, 0)
        self.transition.set_transition_surface(mock_color)

        self.assertIsNotNone(self.transition.transition_surface)
        self.assertEqual(
            self.transition.transition_surface.get_size(), (800, 600)
        )
        self.assertEqual(
            self.transition.transition_surface.get_at((0, 0)), mock_color
        )

    def test_set_transition_state(self):
        self.transition.set_transition_state(True)
        self.assertTrue(self.transition.in_transition)

        self.transition.set_transition_state(False)
        self.assertFalse(self.transition.in_transition)

    @patch("pygame.Surface")
    def test_draw_with_transition(self, MockSurface):
        mock_surface = MagicMock()
        mock_transition_surface = MockSurface.return_value
        self.transition.set_transition_surface((0, 0, 0, 255))
        self.transition.set_transition_state(True)

        self.transition.transition_surface = MockSurface()
        self.transition.transition_alpha = 100
        self.transition.draw(mock_surface)

        mock_transition_surface.set_alpha.assert_called_with(100)
        mock_surface.blit.assert_called_with(mock_transition_surface, (0, 0))

    @patch("pygame.Surface")
    def test_alpha_change_during_fade(self, MockSurface):
        color = (0, 0, 0, 255)
        self.transition.fade_out(1.0, color)

        self.mock_world.animate.assert_called_with(
            self.transition,
            transition_alpha=255,
            initial=0,
            duration=1.0,
            round_values=True,
        )

    @patch("pygame.Surface")
    def test_fade_out(self, MockSurface):
        mock_color = (0, 0, 0, 255)
        self.transition.fade_out(1.0, mock_color, self.mock_world.player)

        self.mock_world.animate.assert_called_with(
            self.transition,
            transition_alpha=255,
            initial=0,
            duration=1.0,
            round_values=True,
        )
        self.mock_world.movement.stop_char.assert_called_with(
            self.mock_world.player
        )
        self.mock_world.movement.lock_controls.assert_called_with(
            self.mock_world.player
        )
        self.assertTrue(self.transition.in_transition)

    @patch("pygame.Surface")
    def test_fade_in(self, MockSurface):
        mock_color = (0, 0, 0, 255)
        self.transition.fade_in(1.0, mock_color)

        self.mock_world.animate.assert_called_with(
            self.transition,
            transition_alpha=0,
            initial=255,
            duration=1.0,
            round_values=True,
        )
        self.mock_world.task.assert_called()
        self.assertFalse(self.transition.in_transition)

    @patch("pygame.Surface")
    def test_fade_and_teleport(self, MockSurface):
        mock_color = (0, 0, 0, 255)
        mock_teleport = MagicMock()
        self.transition.fade_and_teleport(
            1.0, mock_color, self.mock_world.player, mock_teleport
        )

        self.mock_world.animate.assert_called_with(
            self.transition,
            transition_alpha=255,
            initial=0,
            duration=1.0,
            round_values=True,
        )
        self.mock_world.task.assert_called_with(mock_teleport, 1.0)

        chained_task = self.mock_world.task.return_value.chain
        chained_task.assert_called()

    @patch("pygame.Surface")
    def test_draw(self, MockSurface):
        mock_surface = MagicMock()
        mock_transition_surface = MockSurface.return_value
        self.transition.set_transition_surface((0, 0, 0, 255))
        self.transition.set_transition_state(True)

        self.transition.transition_surface = MockSurface()
        self.transition.transition_alpha = 128

        self.transition.draw(mock_surface)

        mock_transition_surface.set_alpha.assert_called_with(128)
        mock_surface.blit.assert_called_with(mock_transition_surface, (0, 0))

    def test_no_draw_when_not_in_transition(self):
        mock_surface = MagicMock()
        self.transition.set_transition_state(False)

        self.transition.draw(mock_surface)

        mock_surface.blit.assert_not_called()
