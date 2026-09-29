# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.ui.combat_notifier import CombatNotifier, TextAnimationManager


@pytest.fixture
def state():
    s = MagicMock()
    s.client.push_state = MagicMock()
    s.task = MagicMock()
    return s


@pytest.fixture
def alert_manager():
    a = MagicMock()
    a.alert = MagicMock()
    return a


@pytest.fixture
def text_area():
    return MagicMock()


@pytest.fixture
def notifier(state, alert_manager):
    return CombatNotifier(
        state=state,
        text_anim_manager=TextAnimationManager(),
        alert_manager=alert_manager,
        lock_update=True,
    )


def test_show_message_queues_text_animation(notifier, text_area):
    notifier.show_message_and_wait_for_input("Hello!", text_area)
    assert len(notifier.text_anim.text_queue) == 1
    anim, duration = notifier.text_anim.text_queue[0]
    anim()
    notifier.alert_manager.alert.assert_called_once_with("Hello!", text_area)


def test_show_message_schedules_wait_for_input(notifier, state, text_area):
    notifier.show_message_and_wait_for_input("Test", text_area)
    assert state.task.call_count == 1
    args, kwargs = state.task.call_args
    assert "WaitForInputState" in str(args[0])


def test_show_message_no_lock_does_not_schedule(notifier, state, text_area):
    notifier.show_message_and_wait_for_input(
        "Test", text_area, override_lock=False
    )
    state.task.assert_not_called()


def test_trigger_xp_and_wait_for_input(notifier, state, text_area):
    notifier.text_anim.add_xp_message("XP +10")
    notifier.text_anim.add_xp_message("XP +20")
    notifier.trigger_xp_and_wait_for_input(text_area, delay=1.0)
    assert state.task.call_count == 1


def test_show_message_ignores_empty(notifier, text_area):
    notifier.show_message_and_wait_for_input("", text_area)
    assert len(notifier.text_anim.text_queue) == 0
    notifier.alert_manager.alert.assert_not_called()


def test_show_message_override_lock_true(notifier, state, text_area):
    notifier.show_message_and_wait_for_input(
        "Test", text_area, override_lock=True
    )
    state.task.assert_called_once()


def test_show_message_override_lock_false(notifier, state, text_area):
    notifier.show_message_and_wait_for_input(
        "Test", text_area, override_lock=False
    )
    state.task.assert_not_called()


def test_trigger_xp_schedules_one_task(notifier, state, text_area):
    notifier.text_anim.add_xp_message("XP +10")
    notifier.trigger_xp_and_wait_for_input(text_area, delay=1.0)
    assert state.task.call_count == 1
