# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from pygame import SRCALPHA
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.monster import MonsterSpriteHandler


class TestMonsterSpriteHandler(unittest.TestCase):
    def setUp(self):
        self.slug = "rockitten"
        self.front_path = "gfx/sprites/battle/front"
        self.back_path = "gfx/sprites/battle/back"
        self.menu1_path = "gfx/sprites/battle/menu1"
        self.menu2_path = "gfx/sprites/battle/menu2"
        self.flairs = {}

        self.handler = MonsterSpriteHandler(
            slug=self.slug,
            front_path=self.front_path,
            back_path=self.back_path,
            menu1_path=self.menu1_path,
            menu2_path=self.menu2_path,
            flairs=self.flairs,
        )

    @patch(
        "tuxemon.tools.transform_resource_filename",
        return_value="transformed/gfx/sprites/battle/sprite.png",
    )
    def test_get_sprite_path_valid(self, mock_transform):
        sprite_path = self.handler.get_sprite_path("test_sprite")
        self.assertEqual(
            sprite_path, "transformed/gfx/sprites/battle/sprite.png"
        )
        mock_transform.assert_called_once_with("test_sprite.png")

    @patch("tuxemon.graphics.load_sprite")
    def test_load_sprite(self, mock_load_sprite):
        mock_surface = MagicMock()
        mock_surface.image = Surface((100, 100))
        mock_load_sprite.return_value = mock_surface

        sprite = self.handler.load_sprite(
            "valid/gfx/sprites/battle/sprite.png"
        )
        self.assertIn(
            "valid/gfx/sprites/battle/sprite.png", self.handler.sprite_cache
        )
        self.assertEqual(sprite, mock_surface.image)
        mock_load_sprite.assert_called_once_with(
            "valid/gfx/sprites/battle/sprite.png"
        )

    @patch("tuxemon.graphics.load_animated_sprite")
    @patch("tuxemon.tools.transform_resource_filename")
    def test_load_animated_sprite(
        self, mock_transform_resource_filename, mock_load_animated_sprite
    ):
        mock_transform_resource_filename.side_effect = lambda path: path

        mock_sprite = MagicMock()
        mock_load_animated_sprite.return_value = mock_sprite

        animated_sprite = self.handler.load_animated_sprite(
            ["gfx/sprites/battle/frame1", "gfx/sprites/battle/frame2"], 0.25
        )

        self.assertEqual(animated_sprite, mock_sprite)
        mock_transform_resource_filename.assert_any_call(
            "gfx/sprites/battle/frame1.png"
        )
        mock_transform_resource_filename.assert_any_call(
            "gfx/sprites/battle/frame2.png"
        )
        mock_load_animated_sprite.assert_called_once_with(
            ["gfx/sprites/battle/frame1.png", "gfx/sprites/battle/frame2.png"],
            0.25,
            prepare.SCALE,
        )

    @patch("tuxemon.graphics.load_sprite")
    def test_get_sprite_with_flairs(self, mock_load_sprite):
        base_surface = Surface((100, 100))
        flair_surface = Surface((50, 50), SRCALPHA)

        mock_base = MagicMock()
        mock_base.image = base_surface
        mock_flair = MagicMock()
        mock_flair.image = flair_surface

        mock_load_sprite.side_effect = [mock_base, mock_flair]

        sprite = self.handler.get_sprite("front")
        self.assertEqual(sprite.image.get_size(), (100, 100))
        mock_load_sprite.assert_any_call(self.front_path)

    @patch("tuxemon.graphics.load_and_scale")
    def test_load_sprites(self, mock_load_and_scale):
        mock_surface = Surface((100, 100))
        mock_load_and_scale.return_value = mock_surface

        sprites = self.handler.load_sprites()
        self.assertIn("front", sprites)
        self.assertIn("back", sprites)
        self.assertIn("menu01", sprites)
        self.assertIn("menu02", sprites)
        mock_load_and_scale.assert_any_call(self.front_path, prepare.SCALE)
        mock_load_and_scale.assert_any_call(self.back_path, prepare.SCALE)
        mock_load_and_scale.assert_any_call(self.menu1_path, prepare.SCALE)
        mock_load_and_scale.assert_any_call(self.menu2_path, prepare.SCALE)

        self.assertEqual(len(sprites), 4)
        self.assertIn("front", sprites)
        self.assertIn("back", sprites)
        self.assertIn("menu01", sprites)
        self.assertIn("menu02", sprites)

    @patch("tuxemon.graphics.load_sprite")
    def test_sprite_cache_usage(self, mock_load_sprite):
        mock_surface = MagicMock()
        mock_surface.image = Surface((100, 100))
        mock_load_sprite.return_value = mock_surface

        sprite1 = self.handler.load_sprite(self.front_path)
        sprite2 = self.handler.load_sprite(self.front_path)

        self.assertIs(sprite1, sprite2)
        mock_load_sprite.assert_called_once_with(self.front_path)

    @patch("tuxemon.graphics.load_sprite")
    def test_empty_flairs(self, mock_load_sprite):
        mock_surface = MagicMock()
        mock_surface.image = Surface((100, 100))
        mock_load_sprite.return_value = mock_surface

        self.handler.flairs = {}
        sprite = self.handler.get_sprite("front")
        self.assertIsNotNone(sprite.image)
        self.assertEqual(sprite.image.get_size(), (100, 100))
