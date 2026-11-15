# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from pygame.sprite import Group

from tuxemon.animation import (
    Animation,
    ConditionalTask,
    DelayTask,
    LoopTask,
    RaceTask,
    RetryTask,
    ScheduledFunction,
    ScheduleType,
    Task,
    TaskBase,
    TaskParallel,
    TaskSequence,
)

logger = logging.getLogger(__name__)


class AnimationGroup:
    def __init__(self) -> None:
        self._group: Group[TaskBase] = Group()

    def animate(self, *targets: Any, **kwargs: Any) -> Animation:
        ani = Animation(*targets, **kwargs)
        self._group.add(ani)
        return ani

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
        """
        Create a task for this state.

        Tasks are processed even while state is inactive.
        If you want to pass positional arguments, use functools.partial.

        Parameters:
            func: Function to be called.
            on_finish: Optional callback to execute when the task finishes.
            on_update: Optional callback to execute on every update.
            interval: Time between callbacks.
            times: Number of intervals.
            kwargs: Additional keyword parameters to schedule other callbacks
                (e.g., 'on abort').

        Returns:
            The created task.
        """
        if not callable(func):
            raise ValueError("Must provide a function to be called")

        task = Task(func, interval=interval, times=times)
        callbacks_to_schedule: dict[ScheduleType, ScheduledFunction] = {}

        if on_finish is not None:
            callbacks_to_schedule[ScheduleType.ON_FINISH] = on_finish
        if on_update is not None:
            callbacks_to_schedule[ScheduleType.ON_UPDATE] = on_update

        for key, value in kwargs.items():
            try:
                schedule_type = ScheduleType(key)
                if schedule_type in task._valid_schedules:
                    if callable(value):
                        callbacks_to_schedule[schedule_type] = value
                    else:
                        raise TypeError(
                            f"Callback for '{key}' must be callable."
                        )
                else:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    f"Invalid callback trigger: '{key}'. "
                    f"Valid options: {[s.value for s in task._valid_schedules]}"
                )

        for when, callback in callbacks_to_schedule.items():
            task.schedule(callback, when)
            logger.debug(
                f"Scheduled callback for Task(id={id(task)}) at {when.value}."
            )

        self._group.add(task)
        return task

    def update(self, dt: float) -> None:
        self._group.update(dt)

    def clear(self) -> None:
        """
        Abort any abortable animations/tasks and clear the group.
        """
        for anim in list(self._group):
            if hasattr(anim, "abort"):
                anim.abort()
        self._group.empty()

    def remove_of(self, target: Any) -> None:
        """
        Remove animations whose targets reference `target`, mirroring original behavior.
        """
        animations = {ani for ani in self._group if isinstance(ani, Animation)}
        to_remove = [
            ani
            for ani in animations
            if any(td.target_ref() == target for td in ani.targets)
        ]

        if not to_remove:
            logger.debug(f"No animations found for target: {target}")
        else:
            logger.debug(
                f"Removing {len(to_remove)} animations for target={target}"
            )

        self._group.remove(*to_remove)

    def chain_animations(
        self, *fns: Callable[[], Animation], start_delay: float = 0.0
    ) -> None:
        """
        Chains a sequence of animations together using callbacks.

        Each function in `fns` should be a factory that returns a new
        Animation instance.

        Parameters:
            fns: A series of callables, each returning an Animation instance.
            start_delay: A delay in milliseconds before the first animation starts.
        """
        if not fns:
            logger.warning(
                "Attempted to chain an empty sequence of functions."
            )
            return

        def chain(index: int = 0) -> None:
            if index >= len(fns):
                return

            anim = fns[index]()
            anim.schedule(
                lambda: chain(index + 1), when=ScheduleType.ON_FINISH
            )

        self.task(lambda: chain(0), interval=start_delay, times=1)

    def sequence(self, *tasks: TaskBase) -> TaskSequence:
        """
        Creates and adds a TaskSequence to the group.

        The sequence executes the provided tasks one after another,
        finishing when the last task is complete.

        Parameters:
            *tasks: TaskBase instances (Task, Animation, TaskParallel, etc.).

        Returns:
            The created TaskSequence.
        """
        if not tasks:
            logger.warning("Attempted to create an empty TaskSequence.")
            seq = TaskSequence()
            self._group.add(seq)
            return seq

        seq = TaskSequence(*tasks)
        self._group.add(seq)
        return seq

    def parallel(self, *tasks: TaskBase) -> TaskParallel:
        """
        Creates and adds a TaskParallel to the group.

        The parallel group executes all provided tasks simultaneously,
        finishing only when ALL tasks are complete (finished or aborted).

        Parameters:
            *tasks: TaskBase instances (Task, Animation, TaskSequence, etc.).

        Returns:
            The created TaskParallel.
        """
        if not tasks:
            logger.warning("Attempted to create an empty TaskParallel.")
            para = TaskParallel()
            self._group.add(para)
            return para

        para = TaskParallel(*tasks)
        self._group.add(para)
        return para

    def loop(self, task: TaskBase, times: int) -> LoopTask:
        """
        Creates and adds a LoopTask to the group.

        The child task will be repeated the specified number of times.

        Parameters:
            task: The TaskBase instance to repeat.
            times: The number of times to repeat the task (must be >= 1).

        Returns:
            The created LoopTask.
        """
        loop_task = LoopTask(task, times=times)
        self._group.add(loop_task)
        return loop_task

    def retry(self, task: TaskBase, max_attempts: int) -> RetryTask:
        """
        Creates and adds a RetryTask to the group.

        The child task will be re-executed if it aborts, up to max_attempts.
        Finishes successfully only if the child task finishes normally.

        Parameters:
            task: The TaskBase instance to attempt.
            max_attempts: The maximum number of times to run the task.

        Returns:
            The created RetryTask.
        """
        retry_task = RetryTask(task, max_attempts=max_attempts)
        self._group.add(retry_task)
        return retry_task

    def conditional(
        self,
        predicate: Callable[[], bool],
        true_task: TaskBase,
        false_task: TaskBase,
    ) -> ConditionalTask:
        """
        Creates and adds a ConditionalTask to the group.

        Executes either the true_task or false_task based on the result
        of the predicate function.

        Parameters:
            predicate: A function that returns True or False.
            true_task: Task to run if the predicate is True.
            false_task: Task to run if the predicate is False.

        Returns:
            The created ConditionalTask.
        """
        cond_task = ConditionalTask(predicate, true_task, false_task)
        self._group.add(cond_task)
        return cond_task

    def race(self, *tasks: TaskBase) -> RaceTask:
        """
        Creates and adds a RaceTask to the group.

        Runs all tasks simultaneously, finishing as soon as the first
        task reaches a terminal state (FINISHED or ABORTED). The others are aborted.

        Parameters:
            *tasks: TaskBase instances to race against each other.

        Returns:
            The created RaceTask.
        """
        if len(tasks) < 2:
            logger.warning(
                "RaceTask needs at least two tasks to be effective."
            )

        race_task = RaceTask(*tasks)
        self._group.add(race_task)
        return race_task

    def delay(self, duration: float) -> DelayTask:
        """
        Creates and adds a DelayTask to the group.

        This is a semantic helper for inserting pauses inside sequences
        or parallel groups.

        Parameters:
            duration: The time in seconds to wait.

        Returns:
            The created DelayTask.
        """
        delay_task = DelayTask(duration)
        self._group.add(delay_task)
        return delay_task
