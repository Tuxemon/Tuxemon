# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.money.controller import MoneyController
from tuxemon.money.manager import MoneyManager


@pytest.fixture
def npc_money_pair():
    npc1 = MagicMock()
    npc1.money_controller = MoneyController(npc1)
    npc1.money_controller.money_manager = MoneyManager()

    npc2 = MagicMock()
    npc2.money_controller = MoneyController(npc2)
    npc2.money_controller.money_manager = MoneyManager()

    return npc1, npc2


def test_transfer_money_success(npc_money_pair):
    npc, npc2 = npc_money_pair
    npc.money_controller.money_manager.add_money(100)
    npc.money_controller.transfer_money_to(50, npc2)
    assert npc.money_controller.money_manager.money == 50
    assert npc2.money_controller.money_manager.money == 50


def test_transfer_money_negative_amount(npc_money_pair):
    npc, npc2 = npc_money_pair
    with pytest.raises(ValueError):
        npc.money_controller.transfer_money_to(-10, npc2)


def test_transfer_money_zero_amount(npc_money_pair):
    npc, npc2 = npc_money_pair
    with pytest.raises(ValueError):
        npc.money_controller.transfer_money_to(0, npc2)


def test_transfer_money_insufficient_funds(npc_money_pair):
    npc, npc2 = npc_money_pair
    npc.money_controller.money_manager.add_money(20)

    with pytest.raises(ValueError):
        npc.money_controller.transfer_money_to(50, npc2)

    assert npc.money_controller.money_manager.money == 20
    assert npc2.money_controller.money_manager.money == 0


def test_transfer_bank_success(npc_money_pair):
    npc, npc2 = npc_money_pair
    npc.money_controller.money_manager.deposit_to_bank(100)
    npc.money_controller.transfer_bank_to(50, npc2)
    assert npc.money_controller.money_manager.bank_account == 50
    assert npc2.money_controller.money_manager.bank_account == 50


def test_transfer_bank_insufficient_funds(npc_money_pair):
    npc, npc2 = npc_money_pair
    npc.money_controller.money_manager.deposit_to_bank(20)

    with pytest.raises(ValueError):
        npc.money_controller.transfer_bank_to(50, npc2)

    assert npc.money_controller.money_manager.bank_account == 20
    assert npc2.money_controller.money_manager.bank_account == 0


def test_wallet_transfer_does_not_affect_bank(npc_money_pair):
    npc, npc2 = npc_money_pair
    npc.money_controller.money_manager.add_money(100)
    npc.money_controller.money_manager.deposit_to_bank(200)
    npc.money_controller.transfer_money_to(50, npc2)
    assert npc.money_controller.money_manager.money == 50
    assert npc.money_controller.money_manager.bank_account == 200


def test_bank_transfer_does_not_affect_wallet(npc_money_pair):
    npc, npc2 = npc_money_pair
    npc.money_controller.money_manager.add_money(100)
    npc.money_controller.money_manager.deposit_to_bank(200)
    npc.money_controller.transfer_bank_to(50, npc2)
    assert npc.money_controller.money_manager.money == 100
    assert npc.money_controller.money_manager.bank_account == 150
