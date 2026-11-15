# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from tuxemon.state.animation_group import AnimationGroup

if TYPE_CHECKING:
    from pygame.sprite import Group

    from tuxemon.animation import (
        Animation,
        ScheduledFunction,
        Task,
        TaskBase,
    )


class AnimationMixin:
    """
    A mixin that provides animation and task scheduling capabilities.
    Can be used by States, Sprites, or any game object.
    """

    def __init__(self) -> None:
        super().__init__()
        self.anim = AnimationGroup()
        self._scheduled_task: Task | None = None

    @property
    def animations(self) -> Group[TaskBase]:
        return self.anim._group

    def animate(self, *targets: Any, **kwargs: Any) -> Animation:
        """
        Animate something in this state.

        Animations are processed even while state is inactive.

        Parameters:
            targets: Targets of the Animation.
            kwargs: Attributes and their final value.

        Returns:
            Resulting animation.
        """
        return self.anim.animate(*targets, **kwargs)

    def task(
        self,
        func: ScheduledFunction,
        *,
        on_finish: ScheduledFunction | None = None,
        on_update: ScheduledFunction | None = None,
        interval: float = 0,
        times: int = 1,
        **kwargs: Any,
    ) -> Task:
        return self.anim.task(
            func,
            on_finish=on_finish,
            on_update=on_update,
            interval=interval,
            times=times,
            **kwargs,
        )

    def chain_animations(
        self, *fns: Callable[[], Animation], start_delay: float = 0.0
    ) -> None:
        self.anim.chain_animations(*fns, start_delay=start_delay)

    def remove_animations_of(self, target: Any) -> None:
        """
        Given and object, remove any animations that it is used with.

        Parameters:
            target: Object whose animations should be removed.
        """
        self.anim.remove_of(target)

    def update_animations(self, time_delta: float) -> None:
        """Must be called in the object's main update loop."""
        self.anim.update(time_delta)
