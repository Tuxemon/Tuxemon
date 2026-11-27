# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

from tuxemon.combat.utils import HEAL_AFTER_BATTLE, heal_after_battle


def _make_session() -> MagicMock:
    return MagicMock()


def _make_monster(hp: int = 100, current_hp: int = 50) -> MagicMock:
    mon = MagicMock()
    mon.hp = hp
    mon.current_hp = current_hp
    mon.is_fainted = False
    return mon


def _make_player(
    monsters: list[MagicMock], rule_value: str | None = "true"
) -> MagicMock:
    player = MagicMock()
    player.game_variables = {}
    if rule_value is not None:
        player.game_variables[HEAL_AFTER_BATTLE] = rule_value
    player.monsters = monsters
    return player


class TestHealAfterBattle:
    def test_rule_true_heals_all_monsters(self):
        session = _make_session()
        mon1 = _make_monster(hp=100, current_hp=50)
        mon2 = _make_monster(hp=200, current_hp=75)
        player = _make_player([mon1, mon2], rule_value="true")

        heal_after_battle(session, [player])

        assert mon1.current_hp == 100
        assert mon2.current_hp == 200
        mon1.status.clear_status.assert_called_once_with(session)
        mon2.status.clear_status.assert_called_once_with(session)

    def test_rule_missing_no_heal(self):
        session = _make_session()
        mon = _make_monster(hp=100, current_hp=50)
        player = _make_player([mon], rule_value=None)

        heal_after_battle(session, [player])

        assert mon.current_hp == 50
        mon.status.clear_status.assert_not_called()

    def test_rule_false_no_heal(self):
        session = _make_session()
        mon = _make_monster(hp=100, current_hp=50)
        player = _make_player([mon], rule_value="false")

        heal_after_battle(session, [player])

        assert mon.current_hp == 50
        mon.status.clear_status.assert_not_called()

    def test_two_players_only_rule_player_healed(self):
        session = _make_session()
        mon_rule = _make_monster(hp=100, current_hp=50)
        mon_no_rule = _make_monster(hp=200, current_hp=80)
        player_with_rule = _make_player([mon_rule], rule_value="true")
        player_without_rule = _make_player([mon_no_rule], rule_value=None)

        heal_after_battle(session, [player_with_rule, player_without_rule])

        assert mon_rule.current_hp == 100
        mon_rule.status.clear_status.assert_called_once_with(session)

        assert mon_no_rule.current_hp == 80
        mon_no_rule.status.clear_status.assert_not_called()

    def test_empty_players_no_error(self):
        session = _make_session()

        heal_after_battle(session, [])
