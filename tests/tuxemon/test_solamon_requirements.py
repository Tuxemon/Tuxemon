# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace
from unittest.mock import MagicMock

from tuxemon.launcher import GameLauncher
from tuxemon.solana.manager import SolanaManager


def _meta() -> SimpleNamespace:
    return SimpleNamespace(
        name="tuxemon",
        version="test",
        starting_position=(1, 1),
        starting_map="starting_map.tmx",
        starting_players=["player"],
        starting_money=(1, 2),
        starting_names=["player"],
        sprite="player",
        combat_sheet="player",
    )


def test_wallet_validator() -> None:
    assert SolanaManager.is_valid_wallet_address(
        "11111111111111111111111111111111"
    )
    assert not SolanaManager.is_valid_wallet_address("bad_wallet")


def test_launcher_requires_wallet(monkeypatch) -> None:
    client = MagicMock()
    client.solana_manager.has_wallet_connection.return_value = False
    client.network_manager.is_connected.return_value = True
    launcher = GameLauncher(client)

    launcher.launch(session=MagicMock(), meta=_meta())

    client.push_state.assert_not_called()


def test_launcher_requires_multiplayer(monkeypatch) -> None:
    client = MagicMock()
    client.solana_manager.has_wallet_connection.return_value = True
    client.network_manager.is_connected.return_value = False
    launcher = GameLauncher(client)

    launcher.launch(session=MagicMock(), meta=_meta())

    client.push_state.assert_not_called()
