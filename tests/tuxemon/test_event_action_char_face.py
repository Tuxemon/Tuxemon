# SPDX-License-Identifier: GPL-3.0
from unittest.mock import MagicMock

from tuxemon.event.actions.char_face import CharFaceAction


def test_char_face_stops_when_character_missing() -> None:
    action = CharFaceAction("missing_npc", "down")
    action.stop = MagicMock()
    session = MagicMock()
    session.get_npc.return_value = None

    action.start(session)

    action.stop.assert_called_once()


def test_char_face_stops_when_target_missing() -> None:
    action = CharFaceAction("npc_maple", "missing_target")
    action.stop = MagicMock()
    session = MagicMock()
    character = MagicMock(tile_pos=(0, 0), is_player=False)

    def get_npc(slug):
        return character if slug == "npc_maple" else None

    session.get_npc.side_effect = get_npc

    action.start(session)

    action.stop.assert_called_once()
