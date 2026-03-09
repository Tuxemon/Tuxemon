# SPDX-License-Identifier: GPL-3.0
import logging
from unittest.mock import MagicMock

from tuxemon.event.actions.rename_player import RenamePlayerAction


def test_set_player_name_forces_network_sync_when_connected() -> None:
    action = RenamePlayerAction(character="player")

    network_client = MagicMock()
    network_manager = MagicMock()
    network_manager.is_connected.return_value = True
    network_manager.client = network_client

    client = MagicMock(network_manager=network_manager)
    session = MagicMock(client=client)
    char = MagicMock(session=session)

    action.set_player_name(char, "Ash")

    assert char.name == "Ash"
    network_client.force_sync_player_state.assert_called_once()


def test_set_player_name_logs_rename_and_sync(caplog) -> None:
    action = RenamePlayerAction(character="player")

    network_client = MagicMock()
    network_manager = MagicMock()
    network_manager.is_connected.return_value = True
    network_manager.client = network_client

    client = MagicMock(network_manager=network_manager)
    session = MagicMock(client=client)
    char = MagicMock(session=session)
    char.name = "Red"

    with caplog.at_level(logging.WARNING):
        action.set_player_name(char, "Ash")

    assert "Player rename requested" in caplog.text
    assert "Triggered forced network sync after rename" in caplog.text
