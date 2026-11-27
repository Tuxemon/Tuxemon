# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tuxemon.core.effects.capture import SURE_CAPTURE, CaptureEffect


def _capture(session, target, caught, rule=None):
    session.player.game_variables = (
        {} if rule is None else {SURE_CAPTURE: rule}
    )
    session.player.monsters = []
    item = MagicMock(slug="tuxeball")
    with patch("tuxemon.core.effects.capture.formula") as formula:
        formula.capture.return_value = (caught, 3)
        formula.config_capture.total_shakes = 4
        return CaptureEffect().apply_item_target(session, item, target)


def test_sure_capture_rule_turns_a_miss_into_a_catch():
    session = MagicMock()
    target = MagicMock(slug="helipi", wild=True)
    result = _capture(session, target, caught=False, rule="true")
    assert result.success
    assert result.num_shakes == 4
    session.player.party.add_monster.assert_called_once_with(target, 0)


def test_sure_capture_rule_off_or_absent_leaves_a_miss_a_miss():
    for rule in (None, "false", "off"):
        session = MagicMock()
        result = _capture(session, MagicMock(), caught=False, rule=rule)
        assert not result.success
        session.player.party.add_monster.assert_not_called()


def test_a_catch_is_a_catch_with_or_without_the_rule():
    for rule in (None, "true"):
        session = MagicMock()
        target = MagicMock(slug="helipi", wild=True)
        result = _capture(session, target, caught=True, rule=rule)
        assert result.success
        assert result.num_shakes == 3
