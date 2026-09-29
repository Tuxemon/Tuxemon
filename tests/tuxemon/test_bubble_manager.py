# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest
from pygame import Rect, Surface

from tuxemon.entity.npc import NPC
from tuxemon.map.tuxemon import AbstractMap
from tuxemon.map.view import BubbleManager
from tuxemon.prepare import DisplayContext


@pytest.fixture
def context():
    ctx = MagicMock(spec=DisplayContext)
    ctx.rect = Rect(0, 0, 800, 600)
    ctx.tile_size = (32, 32)

    return ctx


@pytest.fixture
def manager(context):
    return BubbleManager(context=context)


@pytest.fixture
def npc():
    npc = MagicMock(spec=NPC)
    npc.sprite_controller = MagicMock()
    npc.tile_pos = (5, 5)
    sprite_renderer = MagicMock()
    sprite_renderer.rect = Rect(0, 0, 32, 48)
    npc.sprite_controller.get_sprite_renderer.return_value = sprite_renderer
    return npc


@pytest.fixture
def surface_area():
    return Surface((64, 32))


def test_init(manager, context):
    assert manager.layer == 100
    assert manager.offset_divisor == 10
    assert manager.context is context
    assert manager._bubbles == {}


def test_add_bubble(manager, npc, surface_area):
    manager.add_bubble(npc, surface_area)
    assert npc in manager._bubbles
    assert manager._bubbles[npc] is surface_area


def test_remove_bubble(manager, npc, surface_area):
    manager.add_bubble(npc, surface_area)
    manager.remove_bubble(npc)
    assert npc not in manager._bubbles


@pytest.mark.parametrize(
    "present",
    [
        pytest.param(False, id="no_bubble"),
        pytest.param(True, id="has_bubble"),
    ],
)
def test_has_bubble(manager, npc, surface_area, present):
    if present:
        manager.add_bubble(npc, surface_area)
    assert manager.has_bubble(npc) is present


def test_clear_all_bubbles(manager, npc, surface_area):
    npc2 = MagicMock(spec=NPC)
    surface2 = MagicMock(spec=Surface)

    manager.add_bubble(npc, surface_area)
    manager.add_bubble(npc2, surface2)

    manager.clear_all_bubbles()
    assert manager._bubbles == {}


def test_get_rendered_bubbles(
    manager, npc, surface_area, context, monkeypatch
):
    current_map = MagicMock(spec=AbstractMap)

    monkeypatch.setattr(
        "tuxemon.map.view.get_pos_from_tilepos", lambda m, c, v: (100, 200)
    )

    manager.add_bubble(npc, surface_area)
    rendered = manager.get_rendered_bubbles(current_map)

    assert len(rendered) == 1

    surf, rect, layer = rendered[0]

    assert surf is surface_area
    assert isinstance(rect, Rect)
    assert layer == manager.layer

    sprite_renderer = npc.sprite_controller.get_sprite_renderer()
    assert rect.centerx == 100 + sprite_renderer.rect.width // 2
    assert rect.bottom < 200
