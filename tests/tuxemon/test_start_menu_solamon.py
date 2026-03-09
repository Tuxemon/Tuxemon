# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace
from unittest.mock import MagicMock

import tuxemon.states.start as start_module
from tuxemon.states.start import StartState


class _FakeAdd:
    def __init__(self, sink):
        self._sink = sink

    def button(self, **kwargs):
        self._sink.append(kwargs)

    def label(self, **kwargs):
        self._sink.append(kwargs)


class _FakeMenu:
    def __init__(self):
        self.items = []
        self.add = _FakeAdd(self.items)


def _build_state(wallet_connected: bool) -> StartState:
    state = StartState.__new__(StartState)
    state.client = MagicMock()
    state.client.solana_manager.has_wallet_connection.return_value = (
        wallet_connected
    )
    state.client.config = SimpleNamespace(mods=["tuxemon"])
    state.font_type = SimpleNamespace(big=24)
    state._on_afk_threshold = MagicMock()
    state.unsubscribe = MagicMock()
    return state


def test_start_menu_without_wallet_hides_multiplayer() -> None:
    state = _build_state(wallet_connected=False)
    menu = _FakeMenu()
    StartState.add_menu_items(state, menu)

    button_ids = [item["button_id"] for item in menu.items if "button_id" in item]
    assert button_ids == [
        "solamon_wallet_connect",
        "menu_options",
        "exit",
    ]


def test_start_menu_with_wallet_shows_multiplayer() -> None:
    state = _build_state(wallet_connected=True)
    menu = _FakeMenu()
    StartState.add_menu_items(state, menu)

    button_ids = [item["button_id"] for item in menu.items if "button_id" in item]
    assert button_ids == [
        "solamon_wallet_connect",
        "menu_multiplayer",
        "menu_options",
        "exit",
    ]


def test_start_menu_never_shows_load_or_new_game() -> None:
    state = _build_state(wallet_connected=True)
    menu = _FakeMenu()

    StartState.add_menu_items(state, menu)

    button_ids = [item.get("button_id") for item in menu.items if "button_id" in item]
    assert "menu_load" not in button_ids
    assert "menu_new_game" not in button_ids
