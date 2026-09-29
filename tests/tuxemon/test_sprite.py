# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging

import pygame
import pytest
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.sprite import Sprite
from tuxemon.surfanim import SurfaceAnimation


@pytest.fixture(scope="module", autouse=True)
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def surface_10x20() -> Surface:
    s = Surface((10, 20), pygame.SRCALPHA)
    s.fill((255, 0, 0, 255))
    return s


@pytest.fixture
def surface_32x32() -> Surface:
    s = Surface((32, 32), pygame.SRCALPHA)
    s.fill((0, 255, 0, 255))
    return s


class DummyAnimation(SurfaceAnimation):
    """Minimal stand‑in for SurfaceAnimation for testing."""

    def __init__(self, frames: list[Surface]):
        # Bypass parent init; we just need get_current_frame and get_rect
        self._frames = frames
        self._index = 0
        self._time = 0.0

    def update(self, dt: float) -> None:
        self._time += dt
        # simple wrap every 0.1s
        if self._time >= 0.1:
            self._time = 0.0
            self._index = (self._index + 1) % len(self._frames)

    def get_current_frame(self) -> Surface:
        return self._frames[self._index]

    def get_rect(self) -> Rect:
        return self._frames[0].get_rect()


def test_sprite_default_construction():
    s = Sprite()
    assert isinstance(s.rect, Rect)
    assert s.rect.size == (0, 0)
    assert s.visible is True
    assert s.rotation == 0
    assert s.width == 0
    assert s.height == 0
    # image property should not crash even with no original image
    img = s.image
    assert isinstance(img, Surface)


def test_sprite_construction_with_image(surface_10x20):
    s = Sprite(image=surface_10x20)
    assert s._original_image is surface_10x20
    assert s.rect.size == (10, 20)
    assert s.width == 0  # width/height are only synced in update_image
    assert s.height == 0
    # accessing image triggers update_image
    img = s.image
    assert img.get_size() == (10, 20)
    assert s.width == 10
    assert s.height == 20


def test_rect_setter_updates_needs_update(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image  # force initial update
    assert s._needs_update is False
    s.rect = Rect(5, 5, 10, 20)
    assert s.rect.topleft == (5, 5)
    assert s._needs_update is True


def test_rect_setter_none_resets_to_zero_rect():
    s = Sprite()
    s.rect = None
    assert s.rect.size == (0, 0)
    assert s.rect.topleft == (0, 0)


def test_image_returns_dummy_when_invisible(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.visible = False
    img = s.image
    assert img is Sprite._dummy_image
    assert img.get_size() == (0, 0)


def test_image_setter_clears_animation(surface_10x20):
    frames = [Surface((8, 8)), Surface((8, 8))]
    anim = DummyAnimation(frames)
    s = Sprite(animation=anim)
    assert s.animation is anim
    s.image = surface_10x20
    assert s.animation is None
    assert s._original_image is surface_10x20
    assert s.rect.size == (10, 20)


def test_animation_overrides_image(surface_10x20):
    frames = [Surface((8, 8)), Surface((8, 8))]
    frames[0].fill((1, 2, 3))
    frames[1].fill((4, 5, 6))
    anim = DummyAnimation(frames)

    s = Sprite(image=surface_10x20)
    s.animation = anim

    # image property should come from animation, not _image/_original_image
    img = s.image
    assert img.get_size() == (8, 8)
    assert img.get_at((0, 0)) == (1, 2, 3, 255)

    # update animation and check frame change
    s.update(0.1)
    img2 = s.image
    assert img2.get_at((0, 0)) == (4, 5, 6, 255)


def test_animation_sets_rect_size():
    frames = [Surface((16, 24))]
    anim = DummyAnimation(frames)
    s = Sprite(animation=anim)
    assert s.rect.size == (16, 24)


@pytest.mark.parametrize(
    "target_size",
    [
        pytest.param((5, 5), id="5x5"),
        pytest.param((10, 20), id="10x20"),
        pytest.param((40, 80), id="40x80"),
    ],
)
def test_width_height_trigger_rescale(surface_10x20, target_size):
    w, h = target_size
    s = Sprite(image=surface_10x20)
    _ = s.image  # initial update
    assert s._needs_rescale is False

    s.width = w
    s.height = h
    assert s._needs_rescale is True
    assert s._needs_update is True

    img = s.image
    assert img.get_size() == (w, h)
    assert s.width == w
    assert s.height == h
    assert s.rect.size == (w, h)


def test_update_image_preserves_center_on_rescale(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.rect = Rect(100, 200, 10, 20)
    center_before = s.rect.center

    s.width = 30
    s.height = 60
    _ = s.image  # triggers update_image

    assert s.rect.center == center_before
    assert s.rect.size == (30, 60)


@pytest.mark.parametrize(
    "angle",
    [
        pytest.param(0, id="0deg"),
        pytest.param(90, id="90deg"),
        pytest.param(180, id="180deg"),
        pytest.param(270, id="270deg"),
        pytest.param(45, id="45deg"),
    ],
)
def test_rotation_triggers_update(surface_32x32, angle):
    s = Sprite(image=surface_32x32)
    _ = s.image  # initial update
    assert s._needs_update is False

    s.rotation = angle
    assert s.rotation == angle % 360
    assert s._needs_update is True

    img = s.image
    assert isinstance(img, Surface)
    # for 0 rotation, size should match original
    if angle % 360 == 0:
        assert img.get_size() == (32, 32)
    else:
        # rotated square stays square, but size may change due to bounding box
        w, h = img.get_size()
        assert w == h
        assert w >= 32


def test_rotation_preserves_center(surface_32x32):
    s = Sprite(image=surface_32x32)
    s.rect = Rect(50, 60, 32, 32)
    center_before = s.rect.center

    s.rotation = 90
    _ = s.image  # trigger update

    assert s.rect.center == center_before


def test_toggle_visible():
    s = Sprite()
    assert s.visible is True
    s.toggle_visible()
    assert s.visible is False
    s.toggle_visible()
    assert s.visible is True


def test_reset_to_base_image_uses_copy(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.base_image = surface_10x20
    # mutate base_image after setting
    s.base_image.fill((0, 0, 255, 255))

    s.reset_to_base_image()
    img = s.image
    # should be a copy of base_image at reset time
    assert img.get_at((0, 0)) == (0, 0, 255, 255)


def test_reset_to_base_image_logs_warning_when_missing(caplog):
    s = Sprite()
    with caplog.at_level(logging.WARNING):
        s.reset_to_base_image()
    assert any("base_image is not set" in r.message for r in caplog.records)


def test_set_and_get_position(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.set_position(123, 456)
    assert s.get_position() == (123, 456)
    assert s.rect.topleft == (123, 456)


def test_draw_uses_given_rect(surface_10x20):
    s = Sprite(image=surface_10x20)
    target = Surface((100, 100), pygame.SRCALPHA)
    rect = Rect(10, 15, 10, 20)
    modified = s.draw(target, rect)
    assert modified.topleft == rect.topleft
    # pixel at top-left of drawn area should be non‑transparent
    assert target.get_at((10, 15))[3] != 0


def test_draw_default_rect_is_surface_rect(surface_10x20):
    s = Sprite(image=surface_10x20)
    target = Surface((50, 50), pygame.SRCALPHA)
    modified = s.draw(target)
    assert modified.topleft == (0, 0)


def test_animation_toggle_static_to_anim_to_static(surface_10x20):
    # Start with static image
    s = Sprite(image=surface_10x20)
    img1 = s.image
    assert img1.get_size() == (10, 20)

    # Add animation
    frames = [Surface((8, 8)), Surface((8, 8))]
    frames[0].fill((1, 2, 3))
    frames[1].fill((4, 5, 6))
    anim = DummyAnimation(frames)

    s.animation = anim
    img2 = s.image
    assert img2.get_size() == (8, 8)
    assert img2.get_at((0, 0)) == (1, 2, 3, 255)

    # Remove animation → should fall back to original image
    s.animation = None
    img3 = s.image
    assert img3.get_size() == (10, 20)


def test_rotation_bounding_box_non_square():
    surf = Surface((20, 40), pygame.SRCALPHA)
    surf.fill((255, 0, 0, 255))

    s = Sprite(image=surf)
    _ = s.image  # initial update

    s.rotation = 90
    img = s.image

    # Rotating 20x40 by 90 degrees should produce 40x20
    assert img.get_width() == 40
    assert img.get_height() == 20

    # Center must remain stable
    assert s.rect.center == (10, 20)


def test_visibility_toggle_with_animation(surface_10x20):
    frames = [Surface((8, 8)), Surface((8, 8))]
    frames[0].fill((10, 20, 30))
    anim = DummyAnimation(frames)

    s = Sprite(animation=anim)
    assert s.is_visible() is True

    # Hide sprite
    s.toggle_visible()
    assert s.is_visible() is False
    assert s.image is Sprite._dummy_image

    # Show sprite again
    s.toggle_visible()
    assert s.is_visible() is True
    assert s.image.get_size() == (8, 8)


def test_reset_to_base_image_restores_original(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.base_image = surface_10x20.copy()

    # Modify image
    s.width = 5
    _ = s.image

    # Reset
    s.reset_to_base_image()
    img = s.image
    assert img.get_size() == (10, 20)


def test_reset_to_base_image_after_animation(surface_10x20):
    frames = [Surface((8, 8))]
    frames[0].fill((1, 2, 3))
    anim = DummyAnimation(frames)

    s = Sprite(image=surface_10x20)
    s.base_image = surface_10x20.copy()

    s.animation = anim
    _ = s.image  # animation frame

    s.reset_to_base_image()
    img = s.image
    assert img.get_size() == (10, 20)


def test_width_height_preserved_after_rotation(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image  # initial update

    s.width = 50
    s.height = 80
    assert s.width == 50
    assert s.height == 80

    # Rotate the sprite
    s.rotation = 45
    _ = s.image

    # Width/height should still reflect the requested logical size
    assert s.width == 50
    assert s.height == 80


def test_scaling_applies_to_animation_frames():
    frames = [Surface((10, 10)), Surface((10, 10))]
    anim = DummyAnimation(frames)

    s = Sprite(animation=anim)
    _ = s.image  # initial frame

    s.width = 40
    s.height = 20

    img = s.image
    assert img.get_size() == (40, 20)


def test_needs_rescale_clears_after_rotation_without_rescale(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image

    # Trigger rescale flag
    s.width = 10
    s.height = 20
    assert s._needs_rescale is True

    # Rotation should not leave stale rescale flag
    s.rotation = 90
    _ = s.image

    assert s._needs_rescale is False


def test_width_height_not_overwritten_by_rotation_rect_change(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image

    s.width = 30
    s.height = 60

    before = (s.width, s.height)

    s.rotation = 90
    _ = s.image

    after = (s.width, s.height)

    assert before == after


def test_scale_then_rotate_pipeline(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image

    s.width = 40
    s.height = 80
    s.rotation = 90

    img = s.image
    assert img.get_size() == (80, 40)


def test_transform_pipeline_scale_then_rotate(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image

    s.width = 40
    s.height = 80
    s.rotation = 90

    img = s.image
    assert img.get_size() == (80, 40)


def test_rotation_does_not_accumulate_scaling(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.width = 40
    s.height = 80

    _ = s.image
    size1 = s.image.get_size()

    s.rotation = 90
    _ = s.image
    size2 = s.image.get_size()

    s.rotation = 180
    _ = s.image
    size3 = s.image.get_size()

    assert size1 == (40, 80)
    assert size2 == (80, 40)
    assert size3 == (40, 80)


def test_animation_removed_restores_original_size(surface_10x20):
    frames = [Surface((8, 8))]
    anim = DummyAnimation(frames)

    s = Sprite(image=surface_10x20)
    s.animation = anim
    _ = s.image

    s.animation = None
    img = s.image

    assert img.get_size() == (10, 20)


def test_animation_respects_visibility_toggle(surface_10x20):
    frames = [Surface((8, 8))]
    anim = DummyAnimation(frames)

    s = Sprite(animation=anim)
    assert s.image.get_size() == (8, 8)

    s.visible = False
    assert s.image is Sprite._dummy_image

    s.visible = True
    assert s.image.get_size() == (8, 8)


def test_animation_frame_persists_when_reenabled():
    frames = [Surface((8, 8)), Surface((8, 8))]
    anim = DummyAnimation(frames)

    s = Sprite(animation=anim)
    s.update(0.1)  # advance frame
    frame_before = s.image

    s.visible = False
    s.visible = True

    frame_after = s.image
    assert frame_before is frame_after


def test_resizing_preserves_position(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.set_position(200, 300)
    center_before = s.rect.center

    s.width = 40
    s.height = 80
    _ = s.image

    assert s.rect.center == center_before


def test_rotation_preserves_topleft(surface_32x32):
    s = Sprite(image=surface_32x32)
    s.rect.topleft = (100, 200)

    s.rotation = 45
    _ = s.image

    assert s.rect.center == (100 + 16, 200 + 16)


def test_image_cache_stability(surface_10x20):
    s = Sprite(image=surface_10x20)
    img1 = s.image
    rect1 = s.rect.copy()

    img2 = s.image
    rect2 = s.rect.copy()

    assert img1 is img2
    assert rect1 == rect2


def test_rotation_invalidates_cache_once(surface_10x20):
    s = Sprite(image=surface_10x20)
    _ = s.image

    s.rotation = 90
    img1 = s.image
    img2 = s.image

    assert img1 is img2


def test_base_image_is_immutable(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.base_image = surface_10x20.copy()

    s.width = 5
    _ = s.image

    assert s.base_image.get_size() == (10, 20)


def test_reset_base_image_clears_transforms(surface_10x20):
    s = Sprite(image=surface_10x20)
    s.base_image = surface_10x20.copy()

    s.width = 5
    s.height = 5
    s.rotation = 45
    _ = s.image

    s.reset_to_base_image()
    img = s.image

    assert img.get_size() == (10, 20)
