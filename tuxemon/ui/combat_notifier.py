# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from tuxemon.database.rules import config_combat

if TYPE_CHECKING:
    from tuxemon.menu.alert import AlertManager
    from tuxemon.state.state import State
    from tuxemon.ui.text import TextArea

logger = logging.getLogger(__name__)


class TextAnimationManager:
    """
    Manages a queue of timed text animations.
    """

    def __init__(self) -> None:
        self.text_queue: deque[tuple[Callable[[], None], float]] = deque()
        self._text_time_left: float = 0
        self._xp_messages: list[str] = []

    @staticmethod
    def compute_text_anim_time(message: str) -> float:
        """
        Compute required time for a text animation.
        """
        return config_combat.action_time + config_combat.letter_time * len(
            message
        )

    def update_text_animation(self, dt: float) -> None:
        self._text_time_left -= dt
        logger.debug(
            f"Updated animation timer: {self._text_time_left:.2f}s remaining"
        )
        if self._text_time_left <= 0 and self.text_queue:
            next_animation, self._text_time_left = self.text_queue.popleft()
            logger.debug(
                f"Triggering next animation with duration: {self._text_time_left:.2f}s"
            )
            next_animation()

    def add_text_animation(
        self, animation: Callable[..., None], duration: float = 0
    ) -> None:
        self.text_queue.append((animation, duration))
        logger.debug(
            f"Queued new animation. Duration: {duration:.2f}s. Total animations in queue: {len(self.text_queue)}"
        )

    def get_text_animation_time_left(self) -> float:
        return self._text_time_left

    def is_animating(self) -> bool:
        return self._text_time_left > 0 or bool(self.text_queue)

    def add_xp_message(self, message: str) -> None:
        self._xp_messages.append(message)
        logger.debug(
            f"Added XP message: '{message}'. Total XP messages: {len(self._xp_messages)}"
        )

    def trigger_xp_animation(
        self, alert_func: Callable[..., None], text_area: TextArea
    ) -> float | None:
        if not self._xp_messages:
            return None

        combined_message = "\n".join(self._xp_messages)
        duration = self.compute_text_anim_time(combined_message)
        timed_text_animation = partial(alert_func, combined_message, text_area)
        self.add_text_animation(timed_text_animation, duration)
        self._xp_messages.clear()
        return duration


class CombatNotifier:
    """Manages displaying combat messages and handling player input blocking."""

    def __init__(
        self,
        state: State,
        text_anim_manager: TextAnimationManager,
        alert_manager: AlertManager,
        lock_update: bool,
    ):
        self.state = state
        self.text_anim = text_anim_manager
        self.alert_manager = alert_manager
        self._lock_update = lock_update

    def show_message_and_wait_for_input(
        self,
        message: str,
        text_area: TextArea,
        override_lock: bool | None = None,
    ) -> None:
        """
        Displays a combat message and, if configured, pushes a state to wait for player input.
        """
        if not message:
            logger.debug("Attempted to display empty message. Skipping.")
            return

        action_time = self.text_anim.compute_text_anim_time(message)
        logger.debug(
            f"Displaying combat message: '{message}' with duration: {action_time:.2f}s"
        )

        self.text_anim.add_text_animation(
            partial(self.alert_manager.alert, message, text_area), action_time
        )

        should_lock = (
            override_lock if override_lock is not None else self._lock_update
        )
        if should_lock:
            logger.debug(
                "Player input is blocked. Scheduling WaitForInputState."
            )
            self.state.task(
                partial(self.state.client.push_state, "WaitForInputState"),
                interval=action_time,
            )

    def trigger_xp_and_wait_for_input(
        self, text_area: TextArea, delay: float = 3.0
    ) -> None:
        """
        Triggers XP animation and schedules input block based on actual animation duration.
        """

        def trigger_and_block() -> None:
            duration = self.text_anim.trigger_xp_animation(
                self.alert_manager.alert,
                text_area,
            )
            if duration and self._lock_update:
                self.state.task(
                    partial(self.state.client.push_state, "WaitForInputState"),
                    interval=duration,
                )

        self.state.task(trigger_and_block, interval=delay)
