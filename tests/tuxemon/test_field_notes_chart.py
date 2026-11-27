# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import types
from unittest.mock import patch

from tuxemon.states.phone_field_notes import cell_text, met_types


def test_cell_text_double():
    assert cell_text(2.0) == ("2x", "double")


def test_cell_text_half_05():
    assert cell_text(0.5) == ("1/2", "half")


def test_cell_text_half_025():
    assert cell_text(0.25) == ("0.25x", "half")


def test_cell_text_none():
    assert cell_text(0) == ("0", "none")


def test_cell_text_normal():
    assert cell_text(1.0) == ("1", "normal")


def test_cell_text_double_4():
    assert cell_text(4.0) == ("4x", "double")


def test_met_types_empty():
    char = types.SimpleNamespace(
        game_variables={},
        tuxepedia=types.SimpleNamespace(get_monsters=lambda: []),
    )
    with patch("tuxemon.states.phone_field_notes.MonsterModel"):
        assert met_types(char) == set()


def test_met_types_matchups_and_pedia():
    char = types.SimpleNamespace(
        game_variables={"known_matchups": "fire>wood"},
        tuxepedia=types.SimpleNamespace(get_monsters=lambda: ["squink"]),
    )
    with patch("tuxemon.states.phone_field_notes.MonsterModel") as Mock:
        Mock.lookup.return_value = types.SimpleNamespace(types=["water"])
        assert met_types(char) == {"fire", "wood", "water"}


def test_met_types_dual_type():
    char = types.SimpleNamespace(
        game_variables={},
        tuxepedia=types.SimpleNamespace(get_monsters=lambda: ["dualmon"]),
    )
    with patch("tuxemon.states.phone_field_notes.MonsterModel") as Mock:
        Mock.lookup.return_value = types.SimpleNamespace(
            types=["earth", "fire"]
        )
        assert met_types(char) == {"earth", "fire"}


def test_met_types_unknown_slug():
    char = types.SimpleNamespace(
        game_variables={},
        tuxepedia=types.SimpleNamespace(get_monsters=lambda: ["nonexistent"]),
    )
    with patch("tuxemon.states.phone_field_notes.MonsterModel") as Mock:
        Mock.lookup.side_effect = KeyError("nonexistent")
        assert met_types(char) == set()


def test_type_order_puts_unmet_types_last():
    from types import SimpleNamespace

    from tuxemon.states import phone_field_notes as pfn

    elements = {
        slug: SimpleNamespace(name=name)
        for slug, name in [
            ("a", "Zeta"),
            ("b", "Alpha"),
            ("c", "Beta"),
            ("d", "Gamma"),
        ]
    }
    assert pfn.type_order(elements, {"a", "c"}) == ["c", "a", "b", "d"]
    with patch.object(pfn, "SHOW_UNMET_TYPES", False):
        assert pfn.type_order(elements, {"a", "c"}) == ["c", "a"]
