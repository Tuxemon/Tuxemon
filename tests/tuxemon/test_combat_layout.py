# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest
from pygame.rect import Rect

from tuxemon.ui.combat_hud import CombatLayoutManager, MonsterUI, Side


@pytest.fixture
def npc1():
    npc = MagicMock()
    npc.name = "NPC1"
    npc.is_player = False
    return npc


@pytest.fixture
def npc2():
    npc = MagicMock()
    npc.name = "NPC2"
    npc.is_player = False
    return npc


@pytest.fixture
def player_npc():
    npc = MagicMock()
    npc.name = "Player"
    npc.is_player = True
    return npc


@pytest.fixture
def monster1():
    m = MagicMock()
    m.name = "Monster1"
    return m


@pytest.fixture
def monster2():
    m = MagicMock()
    m.name = "Monster2"
    return m


@pytest.fixture
def layouts(npc1, npc2, player_npc):
    return {
        npc1: {
            "home": [Rect(0, 0, 10, 10)],
            "monster_box_home": [Rect(5, 5, 10, 10)],
            "home0": [Rect(0, 0, 10, 10)],
            "monster_box_home0": [Rect(5, 5, 10, 10)],
            "home1": [Rect(10, 0, 10, 10)],
            "monster_box_home1": [Rect(15, 5, 10, 10)],
        },
        npc2: {
            "home": [Rect(20, 0, 10, 10)],
            "monster_box_home": [Rect(25, 5, 10, 10)],
            "home0": [Rect(20, 0, 10, 10)],
            "monster_box_home0": [Rect(25, 5, 10, 10)],
            "home1": [Rect(30, 0, 10, 10)],
            "monster_box_home1": [Rect(35, 5, 10, 10)],
        },
        player_npc: {
            "home": [Rect(40, 0, 10, 10)],
            "monster_box_home": [Rect(45, 5, 10, 10)],
            "home0": [Rect(40, 0, 10, 10)],
            "monster_box_home0": [Rect(45, 5, 10, 10)],
            "home1": [Rect(50, 0, 10, 10)],
            "monster_box_home1": [Rect(55, 5, 10, 10)],
        },
    }


@pytest.fixture
def manager(layouts):
    return CombatLayoutManager(layouts)


def test_assign_player_vs_npc(manager, player_npc, monster1):
    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster1,
        is_double=False,
    )
    ui = manager._monster_ui[monster1]
    assert ui.slot_index == 1
    assert ui.layout_key == "home"
    assert manager._positions[monster1][0] == Side.PLAYER


def test_assign_npc_vs_npc(manager, npc1, npc2, monster1, monster2):
    manager.assign(nr_players=2, npc=npc1, monster=monster1, is_double=False)
    manager.assign(nr_players=2, npc=npc2, monster=monster2, is_double=False)

    ui1 = manager._monster_ui[monster1]
    ui2 = manager._monster_ui[monster2]

    assert ui1.slot_index == 1
    assert ui2.slot_index == 0

    assert manager._positions[monster1][0] == Side.PLAYER
    assert manager._positions[monster2][0] == Side.OPPONENT


def test_get_open_slot(manager, player_npc, monster1):
    slot = manager.get_open_slot(player_npc)
    assert slot == 0

    manager._layout_keys[(player_npc, monster1)] = "home0"
    slot = manager.get_open_slot(player_npc)
    assert slot == 1


def test_get_rect_valid(manager, player_npc):
    rect = manager.get_rect(player_npc, "home")
    assert rect.topleft == (40, 0)


def test_get_rect_missing_key(manager, player_npc):
    with pytest.raises(ValueError):
        manager.get_rect(player_npc, "invalid_key")


def test_assign_hud_and_get_hud(manager, monster1):
    sprite = MagicMock()
    manager.assign_hud(monster1, sprite)
    assert manager.get_hud(monster1) is sprite


def test_delete_hud(manager, monster1):
    sprite = MagicMock()
    sprite.kill = MagicMock()
    manager.assign_hud(monster1, sprite)
    manager.delete_hud(monster1)
    sprite.kill.assert_called_once()
    assert manager.get_hud(monster1) is None


def test_unassign(manager, player_npc, monster1):
    sprite = MagicMock()
    sprite.kill = MagicMock()
    icon = MagicMock()
    icon.kill = MagicMock()

    manager._monster_ui[monster1] = MonsterUI(
        slot_index=0,
        layout_key="home",
        hud_sprite=sprite,
        status_icons=[icon],
        feet_pos=(0, 0),
    )
    manager._positions[monster1] = (Side.PLAYER, 0)
    manager._layout_keys[(player_npc, monster1)] = "home"

    manager.unassign(player_npc, monster1)

    sprite.kill.assert_called_once()
    icon.kill.assert_called_once()
    assert monster1 not in manager._monster_ui
    assert monster1 not in manager._positions
    assert (player_npc, monster1) not in manager._layout_keys


def test_reassign_monster_skips(manager, player_npc, monster1):
    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster1,
        is_double=False,
    )
    original_ui = manager._monster_ui[monster1]

    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster1,
        is_double=False,
    )
    reassigned_ui = manager._monster_ui[monster1]

    assert original_ui is reassigned_ui


def test_get_index_default(manager, monster1):
    index = manager.get_index(monster1)
    assert index == 0


def test_get_key_default(manager, player_npc, monster1):
    key = manager.get_key(player_npc, monster1)
    assert key == "home"


def test_get_feet_position(manager, player_npc, monster1):
    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster1,
        is_double=False,
    )
    feet = manager.get_feet_position(player_npc, monster1)
    assert feet == (45, 5)


def test_unassign_twice_safe(manager, player_npc, monster1):
    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster1,
        is_double=False,
    )
    manager.unassign(player_npc, monster1)
    manager.unassign(player_npc, monster1)


def test_multiple_monsters_same_npc(manager, player_npc, monster1, monster2):
    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster1,
        is_double=False,
    )
    manager.assign(
        nr_players=1,
        npc=player_npc,
        monster=monster2,
        is_double=False,
    )

    index1 = manager.get_index(monster1)
    index2 = manager.get_index(monster2)

    assert index1 == 1
    assert index2 == 1


def test_double_battle_layout_key(manager, player_npc, monster1):
    manager.assign(
        nr_players=2,
        npc=player_npc,
        monster=monster1,
        is_double=True,
    )
    key = manager.get_key(player_npc, monster1)
    assert "home" in key


def test_double_battle_slot_assignment(
    manager, player_npc, monster1, monster2
):
    manager.assign(
        nr_players=2,
        npc=player_npc,
        monster=monster1,
        is_double=True,
    )
    manager.assign(
        nr_players=2,
        npc=player_npc,
        monster=monster2,
        is_double=True,
    )

    ui1 = manager._monster_ui[monster1]
    ui2 = manager._monster_ui[monster2]

    assert ui1.layout_key in ["home0", "home1"]
    assert ui2.layout_key in ["home0", "home1"]
    assert ui1.slot_index != ui2.slot_index


def test_double_battle_feet_position(manager, player_npc, monster1):
    manager.assign(
        nr_players=2,
        npc=player_npc,
        monster=monster1,
        is_double=True,
    )
    feet = manager.get_feet_position(player_npc, monster1)

    assert feet in [(45, 5), (55, 5)]


def test_double_battle_npc_vs_npc(manager, npc1, npc2, monster1, monster2):
    manager.assign(nr_players=2, npc=npc1, monster=monster1, is_double=True)
    manager.assign(nr_players=2, npc=npc2, monster=monster2, is_double=True)

    ui1 = manager._monster_ui[monster1]
    ui2 = manager._monster_ui[monster2]

    assert ui1.layout_key in ["home0", "home1"]
    assert ui2.layout_key in ["home0", "home1"]
    assert ui1.slot_index != ui2.slot_index
