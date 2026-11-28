# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.core.asset import init_assets
from tuxemon.core.effects.give import GiveEffect
from tuxemon.core.effects.locked import LockedMoveEffect
from tuxemon.core.effects.transfer import TransferEffect
from tuxemon.db import BlockedReason, EffectPhase
from tuxemon.monster.status import MonsterStatusHandler
from tuxemon.status.status import Status

POISON_GAIN = "{target} is poisoned."


def make_status(slug, host, gain_cond=None, duration=0):
    """Build a real Status from a mocked db model (avoids loading the db)."""
    init_assets()
    model = MagicMock()
    model.slug = slug
    model.conditions = []
    model.effects = []
    model.modifiers = []
    model.duration = duration
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


def test_gain_text_formats_target(host):
    status = make_status("poison", host, gain_cond=POISON_GAIN)
    assert status.gain_text() == "Rockitten is poisoned."


def test_gain_text_empty_without_gain_cond(host):
    status = make_status("enraged", host, gain_cond=None)
    assert status.gain_text() == ""


def test_apply_status_extras_carry_gain_text(session, host):
    status = make_status("poison", host, gain_cond=POISON_GAIN)

    result = host.status.apply_status(session, status)

    assert result.applied
    assert result.extras == ["Rockitten is poisoned."]


def test_apply_status_extras_empty_without_gain_cond(session, host):
    status = make_status("enraged", host, gain_cond=None)

    result = host.status.apply_status(session, status)

    assert result.applied
    assert result.extras == []


def test_apply_status_extras_empty_when_immune(session, host):
    host.held_item = MagicMock()
    host.held_item.is_immune.return_value = True
    host.held_item.name = "Antidote Charm"
    status = make_status("poison", host, gain_cond=POISON_GAIN)

    result = host.status.apply_status(session, status)

    assert not result.applied
    assert result.blocked_reason == BlockedReason.IMMUNE_BY_ITEM
    assert result.extras == []


def test_apply_status_extras_empty_when_restacked(session, host):
    first = make_status("poison", host, gain_cond=POISON_GAIN)
    host.status.apply_status(session, first)

    again = make_status("poison", host, gain_cond=POISON_GAIN)
    result = host.status.apply_status(session, again)

    assert not result.applied
    assert result.extras == []


def test_gain_text_emitted_after_on_start(session, host):
    status = make_status("poison", host, gain_cond=POISON_GAIN)
    calls = []
    status.use = MagicMock(side_effect=lambda s, phase: calls.append(phase))

    result = host.status.apply_status(session, status)

    assert calls == [EffectPhase.ON_START]
    assert result.extras == ["Rockitten is poisoned."]


@pytest.fixture
def tech():
    technique = MagicMock()
    technique.name = "Poison Sting"
    technique.potency = 1.0
    technique.accuracy = 1.0
    return technique


def use_give(session, tech, target, gain_cond):
    session.client.combat_session.get_tech_hit.return_value = 0.0
    session.client.combat_session.get_target_monsters.return_value = [target]
    status = make_status("poison", target, gain_cond=gain_cond)
    effect = GiveEffect("poison", "enemy_monster")
    with patch("tuxemon.core.effects.give.Status.create", return_value=status):
        return effect.apply_tech_target(session, tech, MagicMock(), target)


def test_give_puts_gain_text_on_tech_message(session, host, tech):
    result = use_give(session, tech, host, POISON_GAIN)

    assert result.success
    assert result.extras == ["Rockitten is poisoned."]


def test_give_no_gain_text_when_immune(session, host, tech):
    host.held_item = MagicMock()
    host.held_item.is_immune.return_value = True
    host.held_item.name = "Antidote Charm"

    result = use_give(session, tech, host, POISON_GAIN)

    assert "Rockitten is poisoned." not in result.extras


def use_transfer(session, tech, user, target, gain_cond):
    session.client.combat_session.get_tech_hit.return_value = 0.0
    user.status.status = [make_status("poison", user, gain_cond=gain_cond)]
    moved = make_status("poison", target, gain_cond=gain_cond)
    effect = TransferEffect("poison", "user_to_target")
    with patch(
        "tuxemon.core.effects.transfer.Status.create", return_value=moved
    ):
        return effect.apply_tech_target(session, tech, user, target)


@pytest.fixture
def other():
    monster = MagicMock()
    monster.name = "Bigfin"
    monster.steps = 0.0
    monster.held_item = None
    monster.status = MonsterStatusHandler()
    return monster


def test_transfer_puts_gain_text_on_tech_message(session, host, other, tech):
    result = use_transfer(session, tech, other, host, POISON_GAIN)

    assert result.success
    assert host.status.has_status("poison")
    assert result.extras == ["Rockitten is poisoned."]


def test_transfer_no_gain_text_without_gain_cond(session, host, other, tech):
    result = use_transfer(session, tech, other, host, None)

    assert result.success
    assert result.extras == []


def test_transfer_no_gain_text_when_already_present(
    session, host, other, tech
):
    host.status.status = [make_status("poison", host, gain_cond=POISON_GAIN)]

    result = use_transfer(session, tech, other, host, POISON_GAIN)

    assert result.extras == []


CONFUSED_GAIN = "{target} is confused."


def use_locked_final_turn(session, tech, user, gain_cond, roll):
    tech.slug = "thrash"
    status = make_status("confused", user, gain_cond=gain_cond)
    effect = LockedMoveEffect(turns=1, confuse_chance=0.5)
    with (
        patch(
            "tuxemon.core.effects.locked.Status.create", return_value=status
        ),
        patch("tuxemon.core.effects.locked.random.random", return_value=roll),
    ):
        return effect.apply_tech_target(session, tech, user, MagicMock())


def test_locked_puts_confusion_gain_text_on_tech_message(session, host, tech):
    result = use_locked_final_turn(session, tech, host, CONFUSED_GAIN, 0.0)

    assert host.status.has_status("confused")
    assert result.extras == ["Rockitten is confused."]


def test_locked_no_gain_text_when_not_confused(session, host, tech):
    result = use_locked_final_turn(session, tech, host, CONFUSED_GAIN, 0.99)

    assert not host.status.has_status("confused")
    assert result.extras == []
