# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock, patch

import pytest

from tuxemon.animation_entity import AnimationInfo, AnimationManager
from tuxemon.db import LoopMode


@pytest.fixture
def mock_animation_model():
    model = Mock()
    model.file = "test_folder"
    model.slug = "test_slug"
    model.frame_x = 16
    model.frame_y = 16
    model.duration = 0.2
    model.rate = 1.0
    model.flip_axes = (False, False)
    return model


@pytest.fixture
def mock_surface_animation():
    anim = Mock()
    anim.copy.return_value = Mock()
    return anim


@pytest.fixture
def manager():
    return AnimationManager()


@pytest.mark.parametrize(
    "loop_input,expected",
    [
        pytest.param(
            LoopMode.INFINITE, LoopMode.INFINITE.value, id="infinite"
        ),
        pytest.param(LoopMode.NO_LOOP, LoopMode.NO_LOOP.value, id="no_loop"),
        pytest.param(3, 3, id="raw_int"),
    ],
)
def test_get_or_create_animation_creates_new(
    manager, mock_animation_model, mock_surface_animation, loop_input, expected
):
    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1", "frame2"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        anim = manager.get_or_create_animation(
            "test_slug",
            duration=0.5,
            loop=loop_input,
        )
        assert anim is mock_surface_animation
        assert "test_slug" in manager._cache
        assert isinstance(manager._cache["test_slug"], AnimationInfo)
        assert manager._cache["test_slug"].animation is mock_surface_animation


def test_get_or_create_animation_uses_cache(
    manager, mock_animation_model, mock_surface_animation
):
    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        first = manager.get_or_create_animation(
            "test_slug", duration=0.5, loop=1
        )
        second = manager.get_or_create_animation(
            "test_slug", duration=0.5, loop=1
        )
        assert first is second
        assert len(manager._cache) == 1


def test_get_or_create_animation_uses_model_duration_when_none(
    manager, mock_animation_model, mock_surface_animation
):
    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ) as create_mock,
    ):
        manager.get_or_create_animation("test_slug", loop=1)
        args, kwargs = create_mock.call_args
        assert args[1] == mock_animation_model.duration


def test_setup_and_play_updates_position_and_layer(
    manager, mock_animation_model, mock_surface_animation
):
    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        manager.setup_and_play(
            slug="test_slug",
            duration=0.5,
            loop=LoopMode.INFINITE,
            position=(5, 10),
            layer=3,
        )
        info = manager._cache["test_slug"]
        assert info.position == (5, 10)
        assert info.layer == 3
        mock_surface_animation.play.assert_called_once()


def test_play_animation_existing(
    manager, mock_animation_model, mock_surface_animation
):
    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        manager.get_or_create_animation("test_slug", duration=0.5, loop=1)
        manager.play_animation("test_slug", position=(1, 2), layer=9)
        info = manager._cache["test_slug"]
        assert info.position == (1, 2)
        assert info.layer == 9
        mock_surface_animation.play.assert_called()


def test_play_animation_missing(manager, caplog):
    manager.play_animation("missing", position=(0, 0), layer=0)
    assert "non-existent animation" in caplog.text


def test_update_all(manager, mock_animation_model, mock_surface_animation):
    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        manager.get_or_create_animation("test_slug", duration=0.5, loop=1)
        manager.update_all(0.16)
        mock_surface_animation.update.assert_called_once_with(0.16)


def test_get_sprite_creates_unique_sprite(
    mock_animation_model, mock_surface_animation
):
    manager = AnimationManager()
    mock_surface_animation.get_rect.return_value.size = (16, 16)
    mock_surface_animation.copy.return_value.get_rect.return_value.size = (
        16,
        16,
    )

    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        sprite = manager.get_sprite("test_slug", loop=LoopMode.NO_LOOP)
        from tuxemon.sprite import Sprite

        assert isinstance(sprite, Sprite)
        mock_surface_animation.copy.assert_called_once()
        unique_instance = mock_surface_animation.copy.return_value
        assert sprite.animation is unique_instance
        unique_instance.play.assert_called_once()


def test_get_sprite_applies_flip_axes(
    mock_animation_model, mock_surface_animation
):
    manager = AnimationManager()
    copied = Mock()
    mock_surface_animation.copy.return_value = copied
    mock_surface_animation.get_rect.return_value.size = (16, 16)
    copied.get_rect.return_value.size = (16, 16)

    with (
        patch(
            "tuxemon.animation_entity.AnimationModel.lookup",
            return_value=mock_animation_model,
        ),
        patch(
            "tuxemon.animation_entity.fetch_asset",
            return_value="path/to/sheet.png",
        ),
        patch(
            "tuxemon.animation_entity.slice_spritesheet",
            return_value=["frame1"],
        ),
        patch(
            "tuxemon.animation_entity.create_animation",
            return_value=mock_surface_animation,
        ),
    ):
        manager.get_sprite("test_slug", loop=1, flip_axes=(True, False))
        copied.flip.assert_called_once_with((True, False))
