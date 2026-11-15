# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.boxes import MonsterBoxes
from tuxemon.entity.npc import NPC, PartyHandler
from tuxemon.game_variables import GameVariablesManager
from tuxemon.platform.const.sizes import KENNEL, PARTY_LIMIT


def fake_mon():
    return MagicMock()


@pytest.fixture
def npc():
    npc = NPC.__new__(NPC)
    npc.is_player = True
    npc._variables = GameVariablesManager()
    npc.monster_boxes = MonsterBoxes()
    npc.monster_boxes.create_box(KENNEL)
    npc.party = PartyHandler(npc.monster_boxes, npc)
    npc.party._monsters = []
    return npc


def test_release_one(npc):
    assert len(npc.monsters) == 0
    assert npc.monster_boxes.get_box_size(KENNEL, "monster") == 0

    mon = fake_mon()
    npc.party.add_monster(mon, 0)
    assert len(npc.monsters) == 1

    npc.party.release_monster(mon)
    assert len(npc.monsters) == 1


def test_release_two(npc):
    monA = fake_mon()
    monB = fake_mon()

    npc.party.add_monster(monA, 0)
    npc.party.add_monster(monB, 1)
    assert len(npc.monsters) == 2

    npc.party.release_monster(monA)
    assert len(npc.monsters) == 1
    assert npc.monsters[0] is monB


@pytest.mark.parametrize(
    "count",
    [
        pytest.param(1, id="count_1"),
        pytest.param(2, id="count_2"),
        pytest.param(3, id="count_3"),
        pytest.param(4, id="count_4"),
        pytest.param(5, id="count_5"),
    ],
)
def test_catch_until_limit(npc, count):
    for _ in range(count):
        npc.party.add_monster(fake_mon(), len(npc.monsters))

    assert len(npc.monsters) == count
    assert npc.monster_boxes.get_box_size(KENNEL, "monster") == 0


def test_catch_multiple_overflow(npc):
    for _ in range(PARTY_LIMIT):
        npc.party.add_monster(fake_mon(), len(npc.monsters))

    assert len(npc.monsters) == PARTY_LIMIT
    assert npc.monster_boxes.get_box_size(KENNEL, "monster") == 0

    npc.party.add_monster(fake_mon(), len(npc.monsters))

    assert len(npc.monsters) == PARTY_LIMIT
    assert npc.monster_boxes.get_box_size(KENNEL, "monster") == 1
