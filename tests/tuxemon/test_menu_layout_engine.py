# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest
from pygame import Rect

from tuxemon.menu.layout_engine import MenuLayoutEngine


class FakeScaling:
    def scale_int(self, value: int) -> int:
        return value


class FakeContext:
    def __init__(self):
        self.scaling = FakeScaling()


class FakeClient:
    def __init__(self):
        self.context = FakeContext()


class FakeSpriteContainer:
    def __init__(self, rect: Rect):
        self._rect = rect
        self.calc_bounding_rect_called = 0

    def calc_bounding_rect(self) -> Rect:
        self.calc_bounding_rect_called += 1
        return self._rect.copy()


class FakeMenu:
    def __init__(
        self,
        rect: Rect,
        shrink_to_items: bool,
        items_rect: Rect,
        sprites_rect: Rect,
        anchors=None,
    ):
        self.rect = rect
        self.shrink_to_items = shrink_to_items
        self._anchors = anchors or []

        self._items = FakeSpriteContainer(items_rect)
        self._sprites = FakeSpriteContainer(sprites_rect)

        self.arrange_items_called = 0
        self.update_cursor_visibility_called = 0
        self.position_rect_called = 0

        self._client = FakeClient()

    def arrange_items(self) -> None:
        self.arrange_items_called += 1

    def update_cursor_visibility(self) -> None:
        self.update_cursor_visibility_called += 1

    def calc_internal_rect(self) -> Rect:
        return self.rect.copy()

    def position_rect(self) -> None:
        self.position_rect_called += 1

    @property
    def menu_items(self):
        return self._items

    @property
    def menu_sprites(self):
        return self._sprites

    @property
    def client(self):
        return self._client


def test_pure_layout_does_not_mutate_rect():
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=False,
        items_rect=Rect(0, 0, 10, 10),
        sprites_rect=Rect(0, 0, 10, 10),
    )

    original = menu.rect.copy()
    result = engine.compute(menu, mutate=False)

    assert result == original
    assert menu.rect == original
    assert menu.arrange_items_called == 1
    assert menu.update_cursor_visibility_called == 1


def test_mutating_layout_changes_rect_when_shrink_to_items():
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=Rect(0, 0, 40, 20),
        sprites_rect=Rect(0, 0, 30, 10),
    )

    result = engine.compute(menu, mutate=True)

    assert result.width == 40 + 18
    assert result.height == 20 + 19
    assert menu.position_rect_called == 1


@pytest.mark.parametrize(
    "items_rect, sprites_rect, expected",
    [
        pytest.param(
            Rect(0, 0, 10, 10),
            Rect(0, 0, 20, 5),
            (20, 10),
            id="wider_sprites",
        ),
        pytest.param(
            Rect(0, 0, 50, 10),
            Rect(0, 0, 10, 40),
            (50, 40),
            id="taller_sprites",
        ),
        pytest.param(
            Rect(0, 0, 30, 30),
            Rect(0, 0, 30, 30),
            (30, 30),
            id="equal_size",
        ),
    ],
)
def test_union_of_items_and_sprites(items_rect, sprites_rect, expected):
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=items_rect,
        sprites_rect=sprites_rect,
    )

    result = engine.compute(menu, mutate=True)

    expected_w = expected[0] + 18
    expected_h = expected[1] + 19

    assert result.width == expected_w
    assert result.height == expected_h


def test_anchors_are_restored_in_pure_mode():
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=Rect(0, 0, 20, 20),
        sprites_rect=Rect(0, 0, 20, 20),
        anchors=[("center", (200, 200))],
    )

    original_anchors = list(menu._anchors)
    engine.compute(menu, mutate=False)

    assert menu._anchors == original_anchors


def test_position_rect_called_only_when_shrink_to_items():
    engine = MenuLayoutEngine()

    # shrink_to_items = False
    menu1 = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=False,
        items_rect=Rect(0, 0, 10, 10),
        sprites_rect=Rect(0, 0, 10, 10),
    )
    engine.compute(menu1, mutate=True)
    assert menu1.position_rect_called == 0

    # shrink_to_items = True
    menu2 = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=Rect(0, 0, 10, 10),
        sprites_rect=Rect(0, 0, 10, 10),
    )
    engine.compute(menu2, mutate=True)
    assert menu2.position_rect_called == 1


def test_cursor_visibility_and_arrange_items_always_called():
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=False,
        items_rect=Rect(0, 0, 10, 10),
        sprites_rect=Rect(0, 0, 10, 10),
    )

    engine.compute(menu, mutate=True)

    assert menu.arrange_items_called == 1
    assert menu.update_cursor_visibility_called == 1
