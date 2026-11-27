# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock

from tuxemon.event.actions.default_variable import DefaultVariableAction


class Vars(dict):
    def set(self, key, value):
        self[key] = value


def _session() -> MagicMock:
    session = MagicMock()
    session.player.game_variables = Vars()
    return session


def test_unset_variable_gets_value():
    session = _session()
    action = DefaultVariableAction(pair="pick:leave")
    action.start(session)
    assert session.player.game_variables["pick"] == "leave"


def test_existing_value_left_alone():
    session = _session()
    session.player.game_variables["pick"] = "yes"
    action = DefaultVariableAction(pair="pick:leave")
    action.start(session)
    assert session.player.game_variables["pick"] == "yes"


def test_empty_string_value_left_alone():
    session = _session()
    session.player.game_variables["pick"] = ""
    action = DefaultVariableAction(pair="pick:leave")
    action.start(session)
    assert session.player.game_variables["pick"] == ""


def test_value_with_colons_keeps_rest():
    session = _session()
    action = DefaultVariableAction(pair="pick:a:b")
    action.start(session)
    assert session.player.game_variables["pick"] == "a:b"


def test_no_colon_does_nothing():
    session = _session()
    action = DefaultVariableAction(pair="pick")
    action.start(session)
    assert "pick" not in session.player.game_variables


def test_empty_variable_name_does_nothing():
    session = _session()
    action = DefaultVariableAction(pair=":x")
    action.start(session)
    assert "" not in session.player.game_variables


def test_empty_value_sets_empty_string():
    session = _session()
    action = DefaultVariableAction(pair="pick:")
    action.start(session)
    assert "pick" in session.player.game_variables
    assert session.player.game_variables["pick"] == ""
