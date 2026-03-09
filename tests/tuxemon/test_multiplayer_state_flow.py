# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace
from unittest.mock import MagicMock

import tuxemon.states.multiplayer as multiplayer_module
from tuxemon.states.multiplayer import MultiplayerSelect


def test_join_selected_server_connects_and_launches(monkeypatch) -> None:
    state = MultiplayerSelect.__new__(MultiplayerSelect)
    state.network = MagicMock()
    state.network.client = MagicMock()
    state.network.client.available_games = [("127.0.0.1", 40081)]
    state.network.client.connect_to_host.return_value = True

    state.client = MagicMock()
    state.client.solana_manager.has_wallet_connection.return_value = True
    state.client.config = SimpleNamespace(mods=["tuxemon"])

    launcher_instance = MagicMock()
    launcher_cls = MagicMock(return_value=launcher_instance)
    monkeypatch.setattr(multiplayer_module, "GameLauncher", launcher_cls)

    state._join_selected_server(0)

    state.network.client.connect_to_host.assert_called_once_with(
        "127.0.0.1", 40081
    )
    launcher_instance.launch.assert_called_once()


def test_join_selected_server_failure_shows_diagnosis(monkeypatch) -> None:
    state = MultiplayerSelect.__new__(MultiplayerSelect)
    state.network = MagicMock()
    state.network.client = MagicMock()
    state.network.client.available_games = [("127.0.0.1", 40081)]
    state.network.client.connect_to_host.return_value = False
    state.network.client.get_connection_error_message.return_value = (
        "server-side refusal at 127.0.0.1:40081 (Connection refused)."
    )

    state.client = MagicMock()

    open_dialog_mock = MagicMock()
    monkeypatch.setattr(multiplayer_module, "open_dialog", open_dialog_mock)

    state._join_selected_server(0)

    open_dialog_mock.assert_called_once()
    args = open_dialog_mock.call_args[0]
    assert "Connection failed to 127.0.0.1:40081" in args[1][0]
    assert "server-side refusal" in args[1][1]
