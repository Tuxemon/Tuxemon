# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Tests for the Tuxepedia evolution line."""

from __future__ import annotations

import pytest

from tuxemon.states.journal_info import format_evolution_line


@pytest.mark.parametrize(
    "label, names, expected",
    [
        pytest.param("No evolution", [], "No evolution", id="none"),
        pytest.param("Evolution", ["Foo"], "Evolution: Foo", id="one"),
        pytest.param(
            "Evolution", ["Foo", "Bar"], "Evolution: Foo, Bar", id="two"
        ),
    ],
)
def test_format_evolution_line(label, names, expected):
    assert format_evolution_line(label, names) == expected
