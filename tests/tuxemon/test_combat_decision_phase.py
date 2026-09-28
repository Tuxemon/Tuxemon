# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections import deque
from unittest.mock import MagicMock

import pytest

from tuxemon.combat.machine import CombatPhase
from tuxemon.states.combat_state import CombatState
from tuxemon.ui.combat_notifier import TextAnimationManager


def make_state(pending_message: bool) -> CombatState:
    """
    A CombatState reduced to what update_phase touches.

    The phase machine is driven by the real TextAnimationManager, so
    "is something still being said" is answered the same way as in game.
    """
    state = CombatState.__new__(CombatState)
    state.phase = CombatPhase.DECISION
    state.text_anim = TextAnimationManager()
    if pending_message:
        state.text_anim.add_text_animation(lambda: None, 2.5)
    state._decision_queue = deque([MagicMock()])
    state.client = MagicMock()
    state.client.active_states = []
    state.handle_pending_actions = MagicMock()
    return state


def test_menu_waits_for_the_rounds_messages():
    """
    A held item firing is announced during the transition into DECISION, so
    the message is still queued on the frame the phase begins. Asking "what
    will X do?" over the top of it reads as the wrong way round.
    """
    state = make_state(pending_message=True)

    state.update_phase()

    state.handle_pending_actions.assert_not_called()


def test_menu_opens_once_nothing_is_left_to_say():
    state = make_state(pending_message=False)

    state.update_phase()

    state.handle_pending_actions.assert_called_once()


def test_menu_opens_after_the_message_has_played():
    state = make_state(pending_message=True)

    state.update_phase()
    state.handle_pending_actions.assert_not_called()

    # drive the queue the way CombatState.update does
    for _ in range(30):
        state.text_anim.update_text_animation(0.1)
    assert not state.text_anim.is_animating()

    state.update_phase()

    state.handle_pending_actions.assert_called_once()


@pytest.mark.parametrize(
    "phase",
    [
        pytest.param(CombatPhase.ACTION, id="action"),
        pytest.param(CombatPhase.POST_ACTION, id="post_action"),
    ],
)
def test_other_phases_are_untouched(phase):
    """The wait is specific to asking for a decision."""
    state = make_state(pending_message=True)
    state.phase = phase
    state.handle_action_queue = MagicMock()

    state.update_phase()

    state.handle_action_queue.assert_called_once()
