# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tuxemon.core.effects.capture import CaptureEffect


def _capture(session, target, caught=True):
    item = MagicMock(slug="tuxeball")
    clone = MagicMock(name="clone")
    with (
        patch("tuxemon.core.effects.capture.formula") as formula,
        patch(
            "tuxemon.core.effects.capture.make_clone", return_value=clone
        ) as make_clone,
    ):
        formula.capture.return_value = (caught, 3)
        result = CaptureEffect().apply_item_target(session, item, target)
    return result, clone, make_clone


def test_catch_adds_a_clone_and_leaves_the_wild_monster_wild():
    session = MagicMock()
    session.player.monsters = []
    target = MagicMock(slug="helipi", wild=True)
    result, clone, make_clone = _capture(session, target)
    assert result.success
    make_clone.assert_called_once_with(target)
    session.player.party.add_monster.assert_called_once_with(clone, 0)
    assert target.wild is True
    target.set_acquisition.assert_not_called()


def test_missed_net_adds_nothing():
    session = MagicMock()
    result, _, make_clone = _capture(session, MagicMock(), caught=False)
    assert not result.success
    make_clone.assert_not_called()
    session.player.party.add_monster.assert_not_called()
