# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.combat.session import CombatSession
from tuxemon.core.asset import init_assets
from tuxemon.core.effects.die import DieEffect
from tuxemon.monster.status import MonsterStatusHandler
from tuxemon.status.status import Status


def make_status(slug, host, gain_cond=None):
    """Build a real Status from a mocked db model (avoids loading the db)."""
    init_assets()
    model = MagicMock()
    model.slug = slug
    model.conditions = []
    model.effects = []
    model.modifiers = []
    model.duration = 0
    model.max_stacks = 5
    model.step_interval = 0
    model.step_effect_value = 0.0
    model.gain_cond = gain_cond
    model.use_success = None
    model.use_failure = None
    model.on_positive_status = None
    model.on_negative_status = None
    model.category = None
    with patch("tuxemon.status.status.StatusModel.lookup", return_value=model):
        return Status.create(slug, host)


@pytest.fixture
def session():
    init_assets()
    return MagicMock()


@pytest.fixture
def host():
    monster = MagicMock()
    monster.name = "Rockitten"
    monster.steps = 0.0
    monster.held_item = None
    monster.status = MonsterStatusHandler()
    return monster


ENRAGED_GAIN = "{target} is enraged."


def use_die(session, target, gain_cond, turn=1):
    session.client.combat_session.turn = turn
    status = make_status("enraged", target, gain_cond=gain_cond)
    effect = DieEffect("enraged")
    with patch("tuxemon.core.effects.die.Status.create", return_value=status):
        return effect.apply_item_target(session, MagicMock(), target)


def test_die_puts_gain_text_on_item_result(session, host):
    result = use_die(session, host, ENRAGED_GAIN)

    assert host.status.has_status("enraged")
    assert result.extras == ["Rockitten is enraged."]


def test_die_no_gain_text_after_first_turn(session, host):
    result = use_die(session, host, ENRAGED_GAIN, turn=2)

    assert not host.status.has_status("enraged")
    assert result.extras == []


def test_check_decisions_returns_held_item_messages(session, host):
    player = MagicMock()
    host.held_item = MagicMock()
    host.held_item.use.return_value.extras = ["Rockitten is enraged."]
    combat = MagicMock()
    combat.active_players = [player]
    combat.field_monsters.get_monsters.return_value = [host]

    messages = CombatSession.check_decisions(combat, session)

    host.held_item.use.assert_called_once_with(session, player, host)
    assert messages == ["Rockitten is enraged."]
