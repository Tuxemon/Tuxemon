# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tuxemon.combat import bets
from tuxemon.combat.bets import (
    LOSE,
    WIN,
    height_text,
    strong_enough,
    taller_than,
)
from tuxemon.event.actions.pupil_bet import PupilBetAction


class Vars(dict):
    """Minimal stand-in for the in-game variable bag."""

    def set(self, key: str, value: object) -> None:
        self[key] = value


# ---------------------------------------------------------------------------
# bets.py – pure helpers
# ---------------------------------------------------------------------------


class TestTallerThan:
    def test_taller_wins(self):
        assert taller_than(12, 10) == WIN

    def test_equal_height_loses(self):
        assert taller_than(10, 10) == LOSE

    def test_shorter_loses(self):
        assert taller_than(8, 10) == LOSE


class TestStrongEnough:
    def test_above_wins(self):
        assert strong_enough(9, 5) == WIN

    def test_equal_wins(self):
        assert strong_enough(5, 5) == WIN

    def test_below_loses(self):
        assert strong_enough(4, 5) == LOSE


class TestHeightText:
    def test_small_cm(self):
        assert height_text(12) == "12 cm"

    def test_rounds_up_to_100(self):
        assert height_text(99.6) == "100 cm"

    def test_exactly_100(self):
        assert height_text(100) == "1.0 m"

    def test_250_meters(self):
        assert height_text(250) == "2.5 m"

    def test_imperial(self):
        assert height_text(250, "imperial") == "8 ft"


# ---------------------------------------------------------------------------
# pupil_bet.py – PupilBetAction
# ---------------------------------------------------------------------------


def _session():
    s = MagicMock()
    s.player.game_variables = Vars()
    s.player.tuxepedia.get_monsters.return_value = []
    s.client.config.unit_measure = "metric"
    s.player.monsters = []
    return s


def _run(action: PupilBetAction, session: MagicMock) -> Vars:
    action.start(session)
    return session.player.game_variables


def _make_monster(hex_id: str, name: str, **stats) -> MagicMock:
    m = MagicMock()
    m.instance_id.hex = hex_id
    m.name = name
    for attr, val in stats.items():
        setattr(m, attr, val)
    return m


class TestSeen:
    """kind='seen' – the player shows a Tuxepedia species."""

    def test_taller_than_bar_wins(self):
        session = _session()
        session.player.game_variables["pick"] = "chickadee"
        session.player.tuxepedia.get_monsters.return_value = ["chickadee"]

        with (
            patch("tuxemon.event.actions.pupil_bet.MonsterModel") as mm,
            patch("tuxemon.event.actions.pupil_bet.T") as tr,
        ):
            mm.lookup.return_value.slug = "chickadee"
            mm.lookup.return_value.height = 12
            tr.translate.side_effect = lambda s: s.capitalize()

            gv = _run(
                PupilBetAction(kind="seen", variable="pick", first="10"),
                session,
            )

        assert gv["ladder_bet_result"] == "win"
        assert gv["ladder_bet_name"] == "Chickadee"
        assert gv["ladder_bet_value"] == "12 cm"

    def test_equal_height_loses(self):
        session = _session()
        session.player.game_variables["pick"] = "chickadee"
        session.player.tuxepedia.get_monsters.return_value = ["chickadee"]

        with (
            patch("tuxemon.event.actions.pupil_bet.MonsterModel") as mm,
            patch("tuxemon.event.actions.pupil_bet.T") as tr,
        ):
            mm.lookup.return_value.slug = "chickadee"
            mm.lookup.return_value.height = 12
            tr.translate.side_effect = lambda s: s.capitalize()

            gv = _run(
                PupilBetAction(kind="seen", variable="pick", first="12"),
                session,
            )

        assert gv["ladder_bet_result"] == "lose"
        assert gv["ladder_bet_name"] == "Chickadee"
        assert gv["ladder_bet_value"] == "12 cm"

    def test_no_choice(self):
        session = _session()
        session.player.game_variables["pick"] = "no_choice"
        session.player.tuxepedia.get_monsters.return_value = ["chickadee"]

        gv = _run(
            PupilBetAction(kind="seen", variable="pick", first="10"),
            session,
        )

        assert gv["ladder_bet_result"] == "none"
        assert "ladder_bet_name" not in gv

    def test_slug_not_in_tuxepedia(self):
        session = _session()
        session.player.game_variables["pick"] = "rattler"
        session.player.tuxepedia.get_monsters.return_value = ["chickadee"]

        gv = _run(
            PupilBetAction(kind="seen", variable="pick", first="10"),
            session,
        )

        assert gv["ladder_bet_result"] == "none"


class TestTeam:
    """kind='team' – the player shows a team monster."""

    def test_melee_above_bar_wins(self):
        session = _session()
        session.player.game_variables["mon"] = "abc123"
        session.player.monsters = [
            _make_monster("abc123", "Gigantoad", melee=9)
        ]

        gv = _run(
            PupilBetAction(
                kind="team", variable="mon", first="melee", second="5"
            ),
            session,
        )

        assert gv["ladder_bet_result"] == "win"
        assert gv["ladder_bet_name"] == "Gigantoad"
        assert gv["ladder_bet_value"] == "9"

    def test_melee_below_bar_loses(self):
        session = _session()
        session.player.game_variables["mon"] = "abc123"
        session.player.monsters = [
            _make_monster("abc123", "Gigantoad", melee=4)
        ]

        gv = _run(
            PupilBetAction(
                kind="team", variable="mon", first="melee", second="5"
            ),
            session,
        )

        assert gv["ladder_bet_result"] == "lose"

    def test_no_choice(self):
        session = _session()
        session.player.game_variables["mon"] = "no_choice"
        session.player.monsters = [
            _make_monster("abc123", "Gigantoad", melee=9)
        ]

        gv = _run(
            PupilBetAction(
                kind="team", variable="mon", first="melee", second="5"
            ),
            session,
        )

        assert gv["ladder_bet_result"] == "none"

    def test_unknown_stat(self):
        session = _session()
        session.player.game_variables["mon"] = "abc123"
        session.player.monsters = [
            _make_monster("abc123", "Gigantoad", melee=9)
        ]

        gv = _run(
            PupilBetAction(
                kind="team", variable="mon", first="luck", second="5"
            ),
            session,
        )

        assert gv["ladder_bet_result"] == "none"


class TestUnknownKind:
    def test_dance(self):
        session = _session()
        session.player.game_variables["mon"] = "abc123"

        gv = _run(
            PupilBetAction(kind="dance", variable="mon", first="5"),
            session,
        )

        assert gv["ladder_bet_result"] == "none"


class TestWeightBets:
    def test_weight_text(self):
        assert bets.weight_text(0.5) == "0.5 kg"
        assert bets.weight_text(24) == "24.0 kg"
        assert bets.weight_text(1, "imperial") == "2.2 lb"

    def test_value_text_by_stat(self):
        assert bets.value_text("weight", 1.26) == "1.3 kg"
        assert bets.value_text("height", 250) == "2.5 m"
        assert bets.value_text("melee", 9) == "9"

    def test_weight_and_height_are_bet_stats(self):
        assert "weight" in bets.BET_STATS and "height" in bets.BET_STATS

    def test_team_weight_bet_shows_kilograms(self):
        session = _session()
        session.player.game_variables["mon"] = "aa"
        session.player.monsters = [_make_monster("aa", "Rocky", weight=24.31)]
        out = _run(
            PupilBetAction(
                kind="team", variable="mon", first="weight", second="0.5"
            ),
            session,
        )
        assert out["ladder_bet_result"] == "win"
        assert out["ladder_bet_name"] == "Rocky"
        assert out["ladder_bet_value"] == "24.3 kg"

    def test_team_weight_bet_lost_when_lighter(self):
        session = _session()
        session.player.game_variables["mon"] = "aa"
        session.player.monsters = [_make_monster("aa", "Pip", weight=0.4)]
        out = _run(
            PupilBetAction(
                kind="team", variable="mon", first="weight", second="0.5"
            ),
            session,
        )
        assert out["ladder_bet_result"] == "lose"
