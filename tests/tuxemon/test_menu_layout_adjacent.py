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
        cursor_margin=(0, 0),
        anchors=None,
    ):
        self.rect = rect
        self.shrink_to_items = shrink_to_items
        self._anchors = anchors or []

        self._items = FakeSpriteContainer(items_rect)
        self._sprites = FakeSpriteContainer(sprites_rect)

        self.cursor_margin = cursor_margin

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
        for attr, value in self._anchors:
            setattr(self.rect, attr, value)

    @property
    def menu_items(self):
        return self._items

    @property
    def menu_sprites(self):
        return self._sprites

    @property
    def client(self):
        return self._client

    def calc_menu_items_rect(self) -> Rect:
        inner = self.calc_internal_rect()
        inflated = inner.inflate(*self.cursor_margin)
        inflated.bottomright = inner.bottomright
        return inflated


def test_calc_menu_items_rect_applies_cursor_margin():
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=False,
        items_rect=Rect(0, 0, 10, 10),
        sprites_rect=Rect(0, 0, 10, 10),
        cursor_margin=(20, 10),
    )

    r = menu.calc_menu_items_rect()

    assert r.width == 100 + 20
    assert r.height == 50 + 10
    assert r.bottomright == menu.rect.bottomright


@pytest.mark.parametrize(
    "anchors, expected_center",
    [
        pytest.param(
            [("center", (200, 200))],
            (200, 200),
            id="center_anchor",
        ),
        pytest.param(
            [("topleft", (10, 10))],
            None,  # computed dynamically
            id="topleft_anchor",
        ),
        pytest.param(
            [("bottomright", (300, 300))],
            None,
            id="bottomright_anchor",
        ),
    ],
)
def test_anchor_application_order(anchors, expected_center):
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=Rect(0, 0, 40, 20),
        sprites_rect=Rect(0, 0, 10, 10),
        anchors=anchors,
    )

    result = engine.compute(menu, mutate=True)

    if expected_center is not None:
        assert result.center == expected_center
        return

    attr, value = anchors[0]

    expected = Rect(0, 0, result.width, result.height)
    setattr(expected, attr, value)

    assert result.center == expected.center


def test_shrink_to_items_preserves_center_before_anchor():
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(100, 100, 100, 50),
        shrink_to_items=True,
        items_rect=Rect(0, 0, 40, 20),
        sprites_rect=Rect(0, 0, 10, 10),
        anchors=[],  # no override
    )

    original_center = menu.rect.center
    result = engine.compute(menu, mutate=True)

    assert result.center == original_center


@pytest.mark.parametrize(
    "items_rect, sprites_rect",
    [
        pytest.param(Rect(0, 0, 0, 0), Rect(0, 0, 0, 0), id="zero_rects"),
        pytest.param(Rect(0, 0, 1, 1), Rect(0, 0, 0, 0), id="one_pixel_item"),
        pytest.param(
            Rect(0, 0, 0, 0), Rect(0, 0, 1, 1), id="one_pixel_sprite"
        ),
    ],
)
def test_union_edge_cases(items_rect, sprites_rect):
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=items_rect,
        sprites_rect=sprites_rect,
    )

    result = engine.compute(menu, mutate=True)

    # Must be >= padding
    assert result.width >= 18
    assert result.height >= 19


def test_padding_constants_are_applied():
    engine = MenuLayoutEngine()
    menu = FakeMenu(
        rect=Rect(0, 0, 100, 50),
        shrink_to_items=True,
        items_rect=Rect(0, 0, 40, 20),
        sprites_rect=Rect(0, 0, 40, 20),
    )

    result = engine.compute(menu, mutate=True)

    assert result.width == 40 + 18
    assert result.height == 20 + 19
