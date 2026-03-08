# SPDX-License-Identifier: GPL-3.0
from unittest.mock import MagicMock

from tuxemon.money.controller import MoneyController


class DummySession:
    def __init__(self) -> None:
        self._client = MagicMock()
        self.client = self._client


class DummyNPC:
    def __init__(self) -> None:
        self.is_player = True
        self.session = DummySession()


def test_money_changes_emit_currency_events() -> None:
    npc = DummyNPC()
    ctrl = MoneyController(npc)

    ctrl.money_manager.add_money(25)
    ctrl.money_manager.remove_money(10)

    npc.session.client.solana_manager.reward_currency.assert_called_once_with(
        25, "add_money"
    )
    npc.session.client.solana_manager.spend_currency.assert_called_once_with(
        10, "remove_money"
    )
