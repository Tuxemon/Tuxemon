# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

from tuxemon.combat.ranks import (
    parse_rank,
    parse_titles,
    raise_rank,
    reach_rank,
    title_for,
)
from tuxemon.event.actions.rank_show import RankShowAction
from tuxemon.event.actions.rank_up import RankUpAction

TITLES = "Novice:Scribe:Sage:Loremaster"


class Vars(dict):
    """Minimal stand-in for the in-game variable bag."""

    def set(self, key: str, value: object) -> None:
        self[key] = value


def _session() -> MagicMock:
    s = MagicMock()
    s.player.game_variables = Vars()
    return s


class TestHelpers:
    def test_parse_titles(self):
        assert parse_titles("A:B: :C") == ["A", "B", "C"]

    def test_parse_rank_absent_or_garbled_is_zero(self):
        assert parse_rank(None) == 0
        assert parse_rank("x") == 0
        assert parse_rank("-3") == 0
        assert parse_rank("2") == 2

    def test_raise_rank_caps(self):
        assert raise_rank(0, 4) == 1
        assert raise_rank(3, 4) == 4
        assert raise_rank(4, 4) == 4

    def test_title_for(self):
        titles = parse_titles(TITLES)
        assert title_for(titles, 0) is None
        assert title_for(titles, 1) == "Novice"
        assert title_for(titles, 4) == "Loremaster"
        assert title_for(titles, 9) == "Loremaster"
        assert title_for([], 1) is None


class TestRankUp:
    def test_first_win_sets_rank_one_and_title(self):
        s = _session()
        RankUpAction(path="scholar", titles=TITLES).start(s)
        gv = s.player.game_variables
        assert gv["ladder_rank_scholar"] == "1"
        assert gv["ladder_rank_scholar_title"] == "Novice"

    def test_second_win_raises_again(self):
        s = _session()
        for _ in range(2):
            RankUpAction(path="scholar", titles=TITLES).start(s)
        gv = s.player.game_variables
        assert gv["ladder_rank_scholar"] == "2"
        assert gv["ladder_rank_scholar_title"] == "Scribe"

    def test_stops_at_last_title(self):
        s = _session()
        for _ in range(7):
            RankUpAction(path="scholar", titles=TITLES).start(s)
        gv = s.player.game_variables
        assert gv["ladder_rank_scholar"] == "4"
        assert gv["ladder_rank_scholar_title"] == "Loremaster"

    def test_paths_are_independent(self):
        s = _session()
        RankUpAction(path="scholar", titles=TITLES).start(s)
        assert "ladder_rank_keeper" not in s.player.game_variables

    def test_no_titles_changes_nothing(self):
        s = _session()
        RankUpAction(path="scholar", titles="").start(s)
        assert s.player.game_variables == {}

    def test_rank_given_jumps_to_that_rank(self):
        s = _session()
        RankUpAction(path="scholar", titles=TITLES, rank=3).start(s)
        gv = s.player.game_variables
        assert gv["ladder_rank_scholar"] == "3"
        assert gv["ladder_rank_scholar_title"] == "Sage"

    def test_rank_given_keeps_a_higher_rank(self):
        s = _session()
        s.player.game_variables["ladder_rank_scholar"] = "3"
        RankUpAction(path="scholar", titles=TITLES, rank=2).start(s)
        gv = s.player.game_variables
        assert gv["ladder_rank_scholar"] == "3"
        assert gv["ladder_rank_scholar_title"] == "Sage"

    def test_rank_given_capped_at_last_title(self):
        s = _session()
        RankUpAction(path="scholar", titles=TITLES, rank=9).start(s)
        assert s.player.game_variables["ladder_rank_scholar"] == "4"


class TestReachRank:
    def test_reach_rank(self):
        assert reach_rank(0, 2, 6) == 2
        assert reach_rank(4, 2, 6) == 4
        assert reach_rank(1, 8, 6) == 6


class TestRankShow:
    def test_shows_title(self):
        s = _session()
        s.player.game_variables["ladder_rank_scholar_title"] = "Scribe"
        RankShowAction(path="scholar", none_text="no rank yet").start(s)
        assert s.player.game_variables["ladder_rank_show_scholar"] == "Scribe"

    def test_shows_none_text_without_rank(self):
        s = _session()
        RankShowAction(path="scholar", none_text="no rank yet").start(s)
        assert (
            s.player.game_variables["ladder_rank_show_scholar"]
            == "no rank yet"
        )
