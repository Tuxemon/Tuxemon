# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, patch

from pygame import SRCALPHA
from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.monster_dir.sprite import MonsterSpriteHandler


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

    def test_resolve_path_valid(self):
        with patch(
            "tuxemon.tools.transform_resource_filename",
            return_value="resolved/path.png",
        ) as mock_transform:
            path = self.handler.loader.resolve_path("sprite")
            self.assertEqual(path, "resolved/path.png")
            mock_transform.assert_called_once_with("sprite.png")

    @patch("tuxemon.graphics.load_sprite")
    def test_loader_load_sprite(self, mock_load_sprite):
        mock_surface = MagicMock()
        mock_surface.image = Surface((100, 100))
        mock_load_sprite.return_value = mock_surface

        path = "valid/path.png"
        result = self.handler.loader.load(path)
        self.assertEqual(result.get_size(), (100, 100))
        mock_load_sprite.assert_called_once_with(path)

    @patch("tuxemon.graphics.load_animated_sprite")
    @patch(
        "tuxemon.tools.transform_resource_filename", side_effect=lambda p: p
    )
    def test_loader_load_animated_sprite(self, mock_transform, mock_load_anim):
        mock_sprite = MagicMock()
        mock_load_anim.return_value = mock_sprite

        sprite = self.handler.loader.load_animated(
            ["frame1", "frame2"], 0.25, 1.0
        )
        self.assertEqual(sprite, mock_sprite)
        mock_load_anim.assert_called_once()

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
    def test_loader_sprite_cache(self, mock_load_sprite):
        mock_surface = MagicMock()
        mock_surface.image = Surface((100, 100))
        mock_load_sprite.return_value = mock_surface

        result1 = self.handler.loader.load(self.front_path)
        result2 = self.handler.loader.load(self.front_path)

        self.assertIs(result1, result2)
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
