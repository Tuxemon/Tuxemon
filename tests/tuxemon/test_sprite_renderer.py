# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pygame
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.map_view import EntityFacing, SpriteController
from tuxemon.npc import NPC
from tuxemon.surfanim import SurfaceAnimation


class TestSpriteRenderer(TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.npc_template = MagicMock()
        self.npc_template.sprite_name = "adventurer"
        self.npc_template.slug = "adventurer"
        self.npc = MagicMock(spec=NPC)
        self.npc.template = self.npc_template
        self.npc.tile_pos = (10, 20)
        self.npc.moving = False
        self.npc.moverate = 1.0
        self.sprite_controller = SpriteController(self.npc)
        self.sprite_renderer = self.sprite_controller.get_sprite_renderer()

    @patch("tuxemon.graphics.load_and_scale")
    def test_load_sprites_npc(self, mock_load_and_scale):
        mock_surface = MagicMock(spec=Surface)
        mock_surface.get_size.return_value = (32, 32)
        mock_load_and_scale.return_value = mock_surface
        self.sprite_controller.load_sprites(self.npc.template)

        self.assertEqual(len(self.sprite_renderer.standing), 4)
        self.assertEqual(len(self.sprite_renderer.sprite), 4)
        self.assertEqual(self.sprite_renderer.player_width, 80)
        self.assertEqual(self.sprite_renderer.player_height, 160)
        self.assertEqual(self.sprite_renderer.rect.topleft, (10, 20))

    @patch("tuxemon.graphics.load_and_scale")
    def test_load_sprites_interactive_object(self, mock_load_and_scale):
        self.npc_template = MagicMock()
        self.npc_template.sprite_name = "screen"
        self.npc_template.slug = "interactive_obj"
        mock_surface = MagicMock(spec=Surface)
        mock_surface.get_size.return_value = (32, 32)
        mock_load_and_scale.return_value = mock_surface
        self.sprite_controller.load_sprites(self.npc.template)

        self.assertEqual(len(self.sprite_renderer.standing), 4)
        self.assertEqual(len(self.sprite_renderer.sprite), 4)
        self.assertEqual(self.sprite_renderer.player_width, 80)
        self.assertEqual(self.sprite_renderer.player_height, 160)
        self.assertEqual(self.sprite_renderer.rect.topleft, (10, 20))

    @patch("tuxemon.graphics.load_and_scale")
    def test_load_walking_animations(self, mock_load_and_scale):
        mock_surface = MagicMock(spec=Surface)
        mock_load_and_scale.return_value = mock_surface
        self.sprite_renderer._load_walking_animations(self.npc.template)

        self.assertEqual(len(self.sprite_renderer.sprite), 4)
        for anim in self.sprite_renderer.sprite.values():
            self.assertIsInstance(anim, SurfaceAnimation)

    def test_calculate_frame_duration(self):
        # * 1000 / prepare.CONFIG.player_walkrate: This calculates the time
        #  (in milliseconds) it takes for a single "step" in the walking animation.
        # * / 3: The walking animation has 3 distinct frames (two walking poses
        #  and two identical idle poses), so we divide the step time by 3 to get
        # the time per frame.
        # * / 1000: This converts the time from milliseconds to seconds.
        # * * 2: Because the idle frame is repeated, we multiply by 2 to account
        # for the total time spent showing all the frames in the animation.
        prepare.CONFIG.player_walkrate = 2.0
        frame_duration = self.sprite_renderer._calculate_frame_duration()
        self.assertEqual(frame_duration, 1 / 3)

    def test_get_frame_standing(self):
        self.npc.moving = False
        self.mock_standing_surface = Surface((80, 160))
        self.sprite_renderer.standing[EntityFacing.front] = (
            self.mock_standing_surface
        )
        self.mock_surface_animation = MagicMock(spec=SurfaceAnimation)
        self.sprite_renderer.sprite["front_walk"] = self.mock_surface_animation
        frame = self.sprite_renderer.get_frame("front", self.npc)
        self.assertEqual(frame, self.mock_standing_surface)

    @patch("tuxemon.surfanim.SurfaceAnimation.get_current_frame")
    def test_get_frame_walking(self, mock_get_current_frame):
        self.npc.moving = True
        mock_surface = MagicMock(spec=Surface)
        mock_get_current_frame.return_value = mock_surface
        frame = self.sprite_renderer.get_frame("front_walk", self.npc)
        self.assertEqual(frame, mock_surface)

    def test_get_frame_animation_not_found(self):
        with self.assertRaises(ValueError):
            self.sprite_renderer.get_frame("nonexistent_animation", self.npc)

    @patch("tuxemon.graphics.load_and_scale")
    def adventurer_loading_paths(self, mock_load_and_scale):
        mock_load_and_scale.return_value = Surface((1, 1))
        self.sprite_controller.load_sprites(self.npc.template)
        expected_paths = [
            os.path.join("sprites", "adventurer_front.png"),
            os.path.join("sprites", "adventurer_back.png"),
            os.path.join("sprites", "adventurer_left.png"),
            os.path.join("sprites", "adventurer_right.png"),
            os.path.join("sprites", "adventurer_front_walk.000.png"),
            os.path.join("sprites", "adventurer_front.png"),
            os.path.join("sprites", "adventurer_front_walk.001.png"),
            os.path.join("sprites", "adventurer_front.png"),
            os.path.join("sprites", "adventurer_back_walk.000.png"),
            os.path.join("sprites", "adventurer_back.png"),
            os.path.join("sprites", "adventurer_back_walk.001.png"),
            os.path.join("sprites", "adventurer_back.png"),
            os.path.join("sprites", "adventurer_left_walk.000.png"),
            os.path.join("sprites", "adventurer_left.png"),
            os.path.join("sprites", "adventurer_left_walk.001.png"),
            os.path.join("sprites", "adventurer_left.png"),
            os.path.join("sprites", "adventurer_right_walk.000.png"),
            os.path.join("sprites", "adventurer_right.png"),
            os.path.join("sprites", "adventurer_right_walk.001.png"),
            os.path.join("sprites", "adventurer_right.png"),
        ]
        actual_paths = [
            call[0][0] for call in mock_load_and_scale.call_args_list
        ]
        self.assertEqual(actual_paths, expected_paths)
