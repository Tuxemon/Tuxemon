# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace
from unittest.mock import MagicMock

from tuxemon.db import Direction
from tuxemon.network.networking import CharData, EventData, EventType, populate_client


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
