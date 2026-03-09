# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace
from unittest.mock import MagicMock

from tuxemon.db import Direction
from tuxemon.network.networking import CharData, EventData, EventType, populate_client, update_client


def _event(name: str, slug: str) -> EventData:
    return EventData(
        type=EventType.PUSH_SELF,
        event_number=1,
        map_name="spyder_paper_town.tmx",
        char_dict=CharData(
            tile_pos=(4, 8),
            name=name,
            facing=Direction.DOWN,
            running=False,
            slug=slug,
            monsters=[],
            inventory=[],
        ),
    )


def test_populate_client_uses_unique_remote_slug(monkeypatch):
    game = MagicMock()
    game.npc_manager = MagicMock()

    created = []

    def fake_create(_session, _slug):
        npc = SimpleNamespace(
            slug=_slug,
            tile_pos=(4, 8),
            interactions=[],
            is_player=False,
            name="",
            _last_tile_pos=(4, 8),
        )
        created.append(npc)
        return npc

    monkeypatch.setattr("tuxemon.network.networking.NPC.create", fake_create)

    registry = {"c1": {}, "c2": {}}

    npc1 = populate_client("c1", _event("Alex", "player_red"), game, registry)
    npc2 = populate_client("c2", _event("Alex", "player_blue"), game, registry)

    assert npc1.slug == "remote_c1"
    assert npc2.slug == "remote_c2"
    assert npc1.slug != npc2.slug
    assert registry["c1"]["sprite"] is npc1
    assert registry["c2"]["sprite"] is npc2
    assert game.npc_manager.place_npc_on_map.call_count == 2


def test_update_client_applies_remote_position_and_state():
    sprite = SimpleNamespace(
        slug="remote_c1",
        name="Old",
        facing=Direction.UP,
        running=False,
        tile_pos=(0, 0),
        _last_tile_pos=(0, 0),
        monsters=[],
        inventory=[],
    )

    def _set_position(pos):
        sprite.tile_pos = tuple(pos)

    sprite.set_position = _set_position

    char_data = CharData(
        tile_pos=(9, 3),
        name="Remote",
        facing=Direction.LEFT,
        running=True,
        monsters=[],
        inventory=[],
    )

    update_client(sprite, char_data, MagicMock())

    assert sprite.name == "Remote"
    assert sprite.facing == Direction.LEFT
    assert sprite.running is True
    assert sprite.tile_pos == (9, 3)
    assert sprite._last_tile_pos == (9, 3)


def test_update_client_ignores_non_remote_entities():
    sprite = SimpleNamespace(
        slug="npc_red",
        name="Local",
        facing=Direction.UP,
        running=False,
        tile_pos=(1, 1),
        _last_tile_pos=(1, 1),
        monsters=[],
        inventory=[],
    )

    def _set_position(pos):
        sprite.tile_pos = tuple(pos)

    sprite.set_position = _set_position

    char_data = CharData(
        tile_pos=(9, 3),
        name="Remote",
        facing=Direction.LEFT,
        running=True,
        monsters=[],
        inventory=[],
    )

    update_client(sprite, char_data, MagicMock())

    assert sprite.name == "Local"
    assert sprite.facing == Direction.UP
    assert sprite.running is False
    assert sprite.tile_pos == (1, 1)
