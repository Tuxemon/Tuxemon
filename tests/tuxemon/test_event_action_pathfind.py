# SPDX-License-Identifier: GPL-3.0
from unittest.mock import MagicMock

from tuxemon.event.actions.pathfind import PathfindAction


def test_pathfind_action_skips_when_entity_missing() -> None:
    action = PathfindAction("missing_npc", 1, 2)
    action.stop = MagicMock()
    session = MagicMock()
    session.get_npc.return_value = None

    action.start(session)

    action.stop.assert_called_once()


def test_pathfind_action_pathfinds_when_entity_exists() -> None:
    action = PathfindAction("npc_maple", 4, 5)
    session = MagicMock()
    npc = MagicMock()
    session.get_npc.return_value = npc

    action.start(session)

    npc.pathfind.assert_called_once_with((4, 5))
