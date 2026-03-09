# SPDX-License-Identifier: GPL-3.0
from unittest.mock import MagicMock

from tuxemon.event.actions.pathfind_to_char import PathfindToCharAction


def test_pathfind_to_char_stops_when_target_missing() -> None:
    action = PathfindToCharAction("missing_target", "npc_maple")
    action.stop = MagicMock()
    session = MagicMock()
    session.get_npc.side_effect = lambda slug: None

    action.start(session)

    action.stop.assert_called_once()


def test_pathfind_to_char_stops_when_moving_entity_missing() -> None:
    action = PathfindToCharAction("npc_target", "missing_mover")
    action.stop = MagicMock()
    session = MagicMock()
    target = MagicMock(tile_pos=(0, 0))

    def get_npc(slug):
        if slug == "npc_target":
            return target
        return None

    session.get_npc.side_effect = get_npc

    action.start(session)

    action.stop.assert_called_once()
