# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, cast
from weakref import ref

from pygame.rect import Rect
from pygame.sprite import Sprite

from tuxemon.state.animation_transition import AnimationTransition

__all__ = (
    "Task",
    "Animation",
    "TaskSequence",
    "TaskParallel",
    "ConditionalTask",
    "LoopTask",
    "RetryTask",
    "RaceTask",
    "DelayTask",
)

ScheduledFunction = Callable[..., Any]

logger = logging.getLogger(__name__)


class AnimationState(Enum):
    NOT_STARTED = auto()
    RUNNING = auto()
    DELAYED = auto()
    FINISHED = auto()
    ABORTED = auto()


class ScheduleType(Enum):
    ON_UPDATE = "on update"
    ON_FINISH = "on finish"
    ON_ABORT = "on abort"
    ON_INTERVAL = "on interval"


@dataclass
class AnimatedPropertyData:
    """Stores the initial and final values for an animated property."""

    initial: float
    final: float
    true_initial: float
    true_final: float


@dataclass
class AnimatedTargetData:
    """Stores a target object and the properties being animated on it."""

    target_ref: ref[object]
    properties: Mapping[str, AnimatedPropertyData]


def check_number(value: Any) -> float:
    """
    Test if an object is a number.

    Raises ``ValueError`` when ``value`` is not a number.

    Parameters:
        value: Some object.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError


class TaskBase(Sprite, ABC):
    _valid_schedules: Sequence[ScheduleType] = []

    def __init__(self) -> None:
        super().__init__()
        self._state: AnimationState = AnimationState.NOT_STARTED
        self._callbacks: defaultdict[
            ScheduleType,
            list[tuple[ScheduledFunction, tuple[Any, ...], dict[str, Any]]],
        ] = defaultdict(list)

    @abstractmethod
    def update(self, dt: float) -> None:
        """Subclasses must implement update to handle their own timing logic."""

    @abstractmethod
    def finish(self) -> None:
        """Define how the task cleans up when completing normally."""

    @abstractmethod
    def abort(self) -> None:
        """Define how the task cleans up when interrupted."""

    def start(self) -> None:
        """
        Public method to explicitly start a task.
        Sets the state to RUNNING if it was NOT_STARTED.
        Subclasses like Animation should override this for custom logic.
        """
        if self._state is AnimationState.NOT_STARTED:
            self._state = AnimationState.RUNNING

    def schedule(
        self,
        func: ScheduledFunction,
        when: ScheduleType | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Schedule a callback during operation of Task or Animation.

        The callback is any callable object.  You can specify different
        times for the callback to be executed, according to the following:

        * "on update": called each time the Task/Animation is updated.
        * "on finish": called when the Task/Animation completes normally.
        * "on abort": called if the Task/Animation is aborted.
        * "on interval": called each interval for Tasks.

        If when is not passed, it will be the first valid schedule type.

        Parameters:
            func: Callable to schedule.
            when: Time when ``func`` is going to be called.
            args: Positional arguments to pass to the callback.
            kwargs: Keyword arguments to pass to the callback.
        """
        if not callable(func):
            raise TypeError(
                f"Scheduled callback must be callable, got {type(func).__name__}"
            )

        # Normalize string schedule types
        if isinstance(when, str):
            try:
                when = ScheduleType(when)
            except ValueError:
                raise ValueError(
                    f"Invalid time to schedule a callback: '{when}'. "
                    f"Valid options: {[s.value for s in self._valid_schedules]}"
                )

        # Default schedule type
        if when is None:
            if not self._valid_schedules:
                raise RuntimeError(
                    f"{self.__class__.__name__} defines no valid schedule types"
                )
            when = self._valid_schedules[0]

        # Validate schedule type
        if when not in self._valid_schedules:
            raise ValueError(
                f"Invalid time to schedule a callback: '{when.value}'. "
                f"Valid options: {[s.value for s in self._valid_schedules]}"
            )

        self._callbacks[when].append((func, args, kwargs))

    def _execute_callbacks(self, when: ScheduleType) -> None:
        """
        Execute all scheduled callbacks for a given time.
        """
        if when in self._callbacks:
            for func, args, kwargs in self._callbacks[when]:
                try:
                    func(*args, **kwargs)
                except Exception:
                    logger.exception("Scheduled callback failed")

    def kill(self) -> None:
        """Ensure we clear callbacks when the sprite is removed."""
        super().kill()


class Task(TaskBase):
    """
    Execute functions at a later time and optionally loop it.

    This is a silly little class meant to make it easy to create
    delayed or looping events without any complicated hooks into
    pygame's clock or event loop.

    Tasks are created and must be added to a normal pygame group
    in order to function.  This group must be updated, but not
    drawn.

    Setting the interval to 0 cause the callback to be called
    on the next update.

    Because the pygame clock returns milliseconds, the examples
    below use milliseconds.  However, you are free to use whatever
    time unit you wish, as long as it is used consistently.

    Parameters:
        callback: Function to execute each interval.
        interval: Time between callbacks.
        times: Number of intervals.

    Examples:
        >>> task_group = Group()

        >>> # like a delay
        >>> def call_later():
        ...    pass
        >>> task = Task(call_later, 1000)
        >>> task_group.add(task)

        >>> # do something 24 times at 1 second intervals
        >>> task = Task(call_later, 1000, 24)

        >>> # do something every 2.5 seconds forever
        >>> task = Task(call_later, 2500, -1)

        >>> # pass arguments using functools.partial
        >>> from functools import partial
        >>> task = Task(partial(call_later(1,2,3, key=value)), 1000)

        >>> # a task must have at lease on callback, but others can be added
        >>> task = Task(call_later, 2500, -1)
        >>> task.schedule(some_thing_else)

        >>> # chain tasks: when one task finishes, start another one
        >>> task = Task(call_later, 2500)
        >>> task.chain(Task(something_else))

        When chaining tasks, do not add the chained tasks to a group.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_INTERVAL,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(
        self,
        callback: ScheduledFunction,
        interval: float = 0,
        times: int = 1,
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        if interval < 0:
            raise ValueError("interval must be non-negative")
        if times < -1 or times == 0:
            raise ValueError(
                "times must be -1 for infinite loops, or a positive integer (>= 1)"
            )

        super().__init__()

        self._interval = interval
        self._loops = times
        self._duration: float = 0.0
        self._chain: list[Task] = []
        self._state = AnimationState.RUNNING

        self.schedule(callback, ScheduleType.ON_INTERVAL)

    def chain(
        self,
        callback: ScheduledFunction,
        interval: float = 0,
        times: int = 1,
    ) -> Task:
        """
        Schedule a callback to execute when this one is finished

        If you attempt to chain a task to a task that will
        never end, RuntimeError will be raised.

        This is convenience to make a new Task and set to it to
        be added to the "on_finish" list.

        Parameters:
            callback: Function to execute each interval.
            interval: Time between callbacks.
            times: Number of intervals.
        """
        next_task = Task(callback, interval, times)
        self.chain_task(next_task)
        return next_task

    def chain_task(self, *others: Task) -> Sequence[Task]:
        """
        Schedule Task(s) to execute when this one is finished.

        If you attempt to chain a task to a task that will
        never end, RuntimeError will be raised.

        Parameters:
            others: Task instances.

        Returns:
            The sequence of added Tasks.
        """
        if self._loops == -1:
            raise RuntimeError("Cannot chain a task to an infinite loop task.")

        for task in others:
            if not isinstance(task, Task):
                raise TypeError(f"Expected Task, got {type(task).__name__}")
            self._chain.append(task)

        return others

    def update(self, dt: float) -> None:
        """
        Update the Task.

        The unit of time passed must match the one used in the
        constructor.

        Task will not 'make up for lost time'. If an interval
        was skipped because of a lagging clock, then callbacks
        will not be made to account for the missed ones.

        Parameters:
            dt: Time passed since last update.
        """
        if dt < 0:
            return

        if self._state is not AnimationState.RUNNING:
            raise RuntimeError(
                f"Task cannot proceed: expected state "
                f" {AnimationState.RUNNING.name}, but found {self._state.name}."
            )

        self._duration += dt
        self._execute_callbacks(ScheduleType.ON_UPDATE)

        if self._duration >= self._interval:
            self._duration -= self._interval

            if self._loops > 0:
                self._loops -= 1
                self._execute_callbacks(ScheduleType.ON_INTERVAL)

                if self._loops == 0:
                    self.finish()
                    return

            elif self._loops == -1:
                # Infinite loop
                self._execute_callbacks(ScheduleType.ON_INTERVAL)

    def finish(self) -> None:
        """Force task to finish, while executing callbacks."""
        if self._state is not AnimationState.RUNNING:
            return

        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self._execute_chain()
        self._cleanup()

    def is_finish(self) -> bool:
        """
        Returns:
            Whether the task is finished or not.
        """
        return self._state is AnimationState.FINISHED

    def reset_delay(self, new_delay: float) -> None:
        """
        Reset the delay before starting task to make sure time left is
        equal or bigger to the provided value

        Parameters:
            new_delay: the updated delay that should be respected
        """
        time_left = self._interval - self._duration
        if new_delay > time_left:
            self._interval = new_delay
            self._duration = 0.0

    def abort(self) -> None:
        """Force task to finish, without executing 'on interval' callbacks."""
        if self._state in (AnimationState.FINISHED, AnimationState.ABORTED):
            return

        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self._cleanup()

    def _cleanup(self) -> None:
        self._chain.clear()
        self._callbacks.clear()
        super().kill()

    def _execute_chain(self) -> None:
        groups = self.groups()
        for task in self._chain:
            task.add(*groups)


class Animation(TaskBase):
    """
    Change numeric values over time.

    To animate a target sprite/object's position, simply specify
    the target x/y values where you want the widget positioned at
    the end of the animation.  Then call start while passing the
    target as the only parameter.

        >>> ani = Animation(x=100, y=100, duration=1000)
        >>> ani.start(sprite)

    The shorthand method of starting animations is to pass the
    targets as positional arguments in the constructor.

        >>> ani = Animation(sprite.rect, x=100, y=0)

    If you would rather specify relative values, then pass the
    relative keyword and the values will be adjusted for you:

        >>> ani = Animation(x=100, y=100, duration=1000)
        >>> ani.start(sprite, relative=True)

    You can also specify a callback that will be executed when the
    animation finishes:

        >>> ani.schedule(my_function, ScheduleType.ON_FINISH)

    Another optional callback is available that is called after
    each update:

        >>> ani.schedule(post_update_function, ScheduleType.ON_UPDATE)

    Animations must be added to a sprite group in order for them
    to be updated.  If the sprite group that contains them is
    drawn then an exception will be raised, so you should create
    a sprite group only for containing Animations.

    You can cancel the animation by calling ``Animation.abort()``.

    When the animation has finished, then it will remove itself
    from the sprite group that contains it.

    You can optionally delay the start of the animation using the
    delay keyword.


    **Callable Attributes**

    Target values can also be callable.  In this case, there is
    no way to determine the initial value unless it is specified
    in the constructor.  If no initial value is specified, it will
    default to 0.

    Like target arguments, the initial value can also refer to a
    callable.

    NOTE: Specifying an initial value will set the initial value
          for all target names in the constructor.  This
          limitation won't be resolved for a while.


    **Pygame Rects**

    The 'round_values' parameter will be set to True automatically
    if pygame rects are used as an animation target.

    Parameters:
        targets: Any valid python objects.
        delay: Delay time before the animation starts.
        round_values: Whether the values must be rounded to the nearest
            integer before being set.
        duration: Time duration of the animation.
        transition: Transition to use in the animation. Can be the name
            of a method of :class:`AnimationTransition` or a callable
            with the same signature.
        initial: Initial value. Can be numeric or a callable that
            returns a numeric value. If ``None`` the value itself is used.
        relative: If the values are relative to the initial value. That is,
            in order to find the actual value one has to add the initial
            one.
        kwargs: Properties of the ``targets`` to be used, and their values.

    Attributes:
        targets: A list of AnimatedTargetData objects, each containing a target
            reference and a dictionary of animated properties.
        _targets: A list of weak references to the target objects.
        delay: The delay time before the animation starts.
        _state: The current state of the animation (NOT_STARTED, RUNNING, FINISHED, or ABORTED).
        _round_values: Whether the values must be rounded to the nearest integer before being set.
        _duration: The time duration of the animation.
        _transition: The transition function to use in the animation.
        _initial: The initial value. Can be numeric or a callable that returns a numeric value.
        _relative: Whether the values are relative to the initial value.
        _elapsed: The elapsed time since the animation started.

    Methods:
        start: Start the animation on a target sprite/object.
        update: Update the animation.
        finish: Finish the animation and execute callbacks.
        abort: Abort the animation and execute callbacks.
        schedule: Schedule a callback to be executed at a specific time.

    Callbacks:
        ON_UPDATE: Called after each update.
        ON_FINISH: Called when the animation finishes.
        ON_ABORT: Called when the animation is aborted.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    default_duration = 1000.0
    default_transition = "linear"

    def __init__(
        self,
        *targets: object,
        delay: float = 0,
        round_values: bool = False,
        duration: float | None = None,
        transition: str | Callable[[float], float] | None = None,
        initial: float | Callable[[], float] | None = None,
        relative: bool = False,
        yoyo: bool = False,
        yoyo_loops: int = -1,
        **kwargs: Any,
    ) -> None:
        super().__init__()

        self.targets: list[AnimatedTargetData] = []
        self._targets: Sequence[ref[object]] = []

        self.delay = delay
        self._round_values = round_values

        if duration is not None and duration < 0:
            raise ValueError("Duration must be non-negative")

        self._duration = (
            self.default_duration if duration is None else duration
        )
        self._transition = self._resolve_transition(transition)
        self._initial = initial
        self._relative = relative
        self._elapsed: float = 0.0

        if yoyo_loops == 0:
            raise ValueError(
                "yoyo_loops must be -1 or a positive integer (>=1)"
            )

        self._yoyo = yoyo
        self._is_yoyo_reverse: bool = False
        self._yoyo_loops = yoyo_loops
        self._half_cycle_count: int = 0

        if not kwargs:
            raise ValueError(
                "Animation must have at least one property to modify"
            )
        self.props = kwargs

        if targets:
            self.start(*targets)

    def _resolve_transition(
        self, transition: str | Callable[[float], float] | None = None
    ) -> Callable[[float], float]:
        if transition is None:
            transition = self.default_transition
        if isinstance(transition, str):
            transition_func = getattr(AnimationTransition, transition, None)
            if transition_func is None or not callable(transition_func):
                raise ValueError(f"Invalid transition name: {transition}")
            return cast(Callable[[float], float], transition_func)
        if not callable(transition):
            raise TypeError(
                "Provided transition must be a callable function or a valid string identifier"
            )
        return transition

    def _get_value(self, target: object, name: str) -> float:
        if self._initial is None:
            value = getattr(target, name)
        else:
            value = self._initial
        if callable(value):
            value = value()
        return check_number(value)

    def _set_value(self, target: object, name: str, value: float) -> None:
        if self._round_values:
            value = round(value)
        attr = getattr(target, name)
        if callable(attr):
            attr(value)
        else:
            setattr(target, name, value)

    def update(self, dt: float) -> None:

        if self._state in (AnimationState.FINISHED, AnimationState.ABORTED):
            return

        if self._state is not AnimationState.RUNNING:
            return

        if self._duration == 0:
            self.finish()
            return

        self._elapsed += dt

        if self.delay > 0:
            if self._elapsed >= self.delay:
                self._elapsed -= self.delay
                self._gather_initial_values()
                self.delay = 0
            return

        p = min(1.0, self._elapsed / self._duration)
        t = self._transition(p)

        for target_data in self.targets:
            target = target_data.target_ref()
            if target is None:
                continue

            for name, prop_data in target_data.properties.items():
                a, b = prop_data.initial, prop_data.final
                value = (a * (1.0 - t)) + (b * t)
                self._set_value(target, name, value)

        self._execute_callbacks(ScheduleType.ON_UPDATE)

        if p >= 1:
            self.finish()

    def _reverse_cycle(self) -> None:
        """
        Reverse the animation direction by swapping initial and final values
        for every animated property. This preserves the existing yoyo behavior.
        """
        for target_data in self.targets:
            for prop_data in target_data.properties.values():
                prop_data.initial, prop_data.final = (
                    prop_data.final,
                    prop_data.initial,
                )
        self._is_yoyo_reverse = not self._is_yoyo_reverse

    def finish(self) -> None:
        if self._state is not AnimationState.RUNNING:
            return

        for target_data in self.targets:
            target = target_data.target_ref()
            if target:
                for name, prop_data in target_data.properties.items():
                    self._set_value(target, name, prop_data.final)

        if self._yoyo:
            self._half_cycle_count += 1
            max_half_cycles = self._yoyo_loops * 2

            if (
                self._yoyo_loops > 0
                and self._half_cycle_count >= max_half_cycles
            ):
                self._state = AnimationState.FINISHED
                for target_data in self.targets:
                    target = target_data.target_ref()
                    if target:
                        for name, prop_data in target_data.properties.items():
                            self._set_value(
                                target, name, prop_data.true_initial
                            )
                self._execute_callbacks(ScheduleType.ON_FINISH)
                self.kill()
                return

            self._elapsed = 0.0
            self._reverse_cycle()
            return

        # Non-yoyo finish
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        if self._state in (AnimationState.FINISHED, AnimationState.ABORTED):
            return

        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def start(self, *targets: object, **kwargs: Any) -> None:
        """
        Start the animation on a target sprite/object.
        ...
        """
        if self._state is not AnimationState.NOT_STARTED:
            raise RuntimeError("Animation has already been started.")

        if kwargs:
            raise TypeError("start() got an unexpected keyword argument")

        self._state = AnimationState.RUNNING

        self._targets = [ref(t) for t in targets]

        if self.delay == 0:
            self._gather_initial_values()

    def _gather_initial_values(self) -> None:
        """
        Gathers the initial and final values for all animated properties
        on each target and sets the initial values immediately.
        """
        self.targets = []
        local_round_values_for_rect = False

        for target_ref in self._targets:
            target = target_ref()
            if target is None:
                logger.debug(
                    "Animation target has been garbage-collected. Skipping."
                )
                continue

            if isinstance(target, Rect):
                local_round_values_for_rect = True

            properties_map = {}

            for name, value in self.props.items():
                try:
                    initial = self._get_value(target, name)
                    check_number(initial)
                    check_number(value)

                    if self._relative:
                        value += initial

                    properties_map[name] = AnimatedPropertyData(
                        initial=initial,
                        final=value,
                        true_initial=initial,
                        true_final=value,
                    )
                except AttributeError:
                    logger.warning(
                        f"Target {target} does not have attribute '{name}' for animation. Skipping."
                    )
                    continue

            if properties_map:
                self.targets.append(
                    AnimatedTargetData(
                        target_ref=target_ref, properties=properties_map
                    )
                )

        if local_round_values_for_rect:
            self._round_values = True

        for target_data in self.targets:
            target = target_data.target_ref()
            if target is None:
                continue
            for name, prop_data in target_data.properties.items():
                self._set_value(target, name, prop_data.initial)

    def kill(self) -> None:
        self.targets.clear()
        self._targets = []
        self.props.clear()
        super().kill()


class TaskSequence(TaskBase):
    """
    Executes a list of tasks one after another.

    A TaskSequence takes any number of TaskBase instances (e.g. Task,
    Animation, TaskParallel) and runs them in order. Each task runs until it
    reaches FINISHED or ABORTED, after which the sequence automatically
    advances to the next task. When all tasks complete, the sequence itself
    finishes.

    Tasks that require an explicit start() call (such as Animation) are
    automatically started when they become the active task.

    Examples
    --------
    Running simple Tasks in sequence:

        seq = TaskSequence(
            Task(lambda: print("Step 1"), interval=0.5, times=1),
            Task(lambda: print("Step 2"), interval=0.5, times=1),
            Task(lambda: print("Step 3"), interval=0.5, times=1),
        )
        group.add(seq)

    Mixing Tasks and Animations:

        move = Animation(sprite, x=200, duration=1.0)
        fade = Animation(sprite, alpha=0, duration=0.5)

        seq = TaskSequence(
            move,   # starts automatically when sequence begins
            fade,   # starts after move finishes
        )
        group.add(seq)

    Using with TaskParallel:

        seq = TaskSequence(
            TaskParallel(
                Animation(sprite, x=200, duration=1.0),
                Animation(sprite, y=100, duration=1.0),
            ),
            Task(lambda: print("Both animations finished")),
        )
        group.add(seq)

    Notes
    -----
    - A TaskSequence finishes when all internal tasks finish or abort.
    - If a task aborts, the sequence immediately advances to the next task.
    - The sequence itself can be aborted, which aborts the current task.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self, *tasks: TaskBase):
        super().__init__()
        self._queue = list(tasks)
        self._current_task: TaskBase | None = None

        if not self._queue:
            # Empty sequence: nothing to run, consider it finished.
            self._state = AnimationState.FINISHED
        else:
            self._state = AnimationState.NOT_STARTED

    def start(self) -> None:
        super().start()
        self._advance()

    def _advance(self) -> None:
        """Start the next task in the queue."""
        if self._queue:
            self._current_task = self._queue.pop(0)
            self._current_task.start()
        else:
            self._current_task = None
            self.finish()

    def update(self, dt: float) -> None:
        if self._state is AnimationState.NOT_STARTED:
            self.start()

        if self._state is not AnimationState.RUNNING:
            return

        if not self._current_task:
            return

        self._current_task.update(dt)
        self._execute_callbacks(ScheduleType.ON_UPDATE)

        # Advance on FINISHED or ABORTED
        if self._current_task._state in (
            AnimationState.FINISHED,
            AnimationState.ABORTED,
        ):
            self._advance()

            if self._current_task and self._state == AnimationState.RUNNING:
                self._current_task.update(dt)

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        if self._current_task is None and self._queue:
            first = self._queue[0]
            if first._state == AnimationState.RUNNING:
                first.abort()
            else:
                first._state = AnimationState.ABORTED
                first._execute_callbacks(ScheduleType.ON_ABORT)

        elif (
            self._current_task
            and self._current_task._state == AnimationState.RUNNING
        ):
            self._current_task.abort()

        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        self._queue.clear()
        self._current_task = None
        super().kill()


class TaskParallel(TaskBase):
    """
    Executes multiple tasks simultaneously.

    A TaskParallel takes any number of TaskBase instances (e.g. Task,
    Animation, TaskSequence) and runs them at the same time. The parallel
    group finishes only when *all* internal tasks have either finished or
    aborted. Tasks that require an explicit start() call (such as Animation)
    are automatically started when the parallel group begins updating.

    Examples
    --------
    Running multiple Tasks in parallel:

        parallel = TaskParallel(
            Task(lambda: print("Tick A"), interval=0.5, times=3),
            Task(lambda: print("Tick B"), interval=1.0, times=2),
        )
        group.add(parallel)

    Running multiple Animations together:

        move = Animation(sprite, x=200, duration=1.0)
        fade = Animation(sprite, alpha=0, duration=1.0)

        parallel = TaskParallel(move, fade)
        group.add(parallel)

    Mixing Tasks, Animations, and Sequences:

        seq = TaskSequence(
            Animation(sprite, x=300, duration=0.5),
            Task(lambda: print("Sequence finished")),
        )

        parallel = TaskParallel(
            seq,
            Animation(sprite, y=150, duration=1.0),
        )
        group.add(parallel)

    Notes
    -----
    - A TaskParallel finishes only when *all* internal tasks finish or abort.
    - If a task aborts, the parallel group continues running until all tasks
      have reached a terminal state.
    - Aborting the TaskParallel aborts all currently running internal tasks.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self, *tasks: TaskBase) -> None:
        super().__init__()
        self._tasks = list(tasks)

        if not self._tasks:
            self._state = AnimationState.FINISHED
            self._execute_callbacks(ScheduleType.ON_FINISH)
        else:
            self._state = AnimationState.RUNNING

    def update(self, dt: float) -> None:
        if self._state is not AnimationState.RUNNING:
            return

        # Start NOT_STARTED tasks (e.g., Animation)
        for task in self._tasks:
            if task._state == AnimationState.NOT_STARTED:
                task.start()

        # Update all running tasks
        for task in self._tasks:
            if task._state == AnimationState.RUNNING:
                task.update(dt)

        self._execute_callbacks(ScheduleType.ON_UPDATE)

        # Check if all tasks are finished or aborted
        all_done = all(
            task._state in (AnimationState.FINISHED, AnimationState.ABORTED)
            for task in self._tasks
        )

        if all_done:
            self.finish()

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        for task in self._tasks:
            if task._state == AnimationState.RUNNING:
                task.abort()
        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        self._tasks.clear()
        super().kill()


class ConditionalTask(TaskBase):
    """
    Executes one of two tasks based on a boolean predicate.

    The predicate is evaluated once when the task starts. If it returns True,
    the `true_task` is executed; otherwise, the `false_task` is executed.
    Only the selected task runs. When that task finishes or aborts, the
    ConditionalTask finishes as well.

    This is useful for branching logic inside a TaskSequence or TaskParallel.

    Examples
    --------
    Basic branching:

        cond = ConditionalTask(
            lambda: player.hp > 0,
            Task(lambda: print("Player is alive")),
            Task(lambda: print("Player is dead")),
        )
        group.add(cond)

    Using inside a sequence:

        seq = TaskSequence(
            Animation(sprite, x=200, duration=1.0),
            ConditionalTask(
                lambda: sprite.x > 150,
                Task(lambda: print("Reached target")),
                Task(lambda: print("Did not reach target")),
            ),
        )
        group.add(seq)

    Notes
    -----
    - Only one of the two tasks ever runs.
    - The predicate is evaluated once at start(), not every frame.
    - The ConditionalTask finishes when the chosen task finishes or aborts.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(
        self,
        predicate: Callable[[], bool],
        true_task: TaskBase,
        false_task: TaskBase,
    ) -> None:
        super().__init__()
        self._predicate = predicate
        self._true_task = true_task
        self._false_task = false_task
        self._active_task: TaskBase | None = None

    def start(self) -> None:
        super().start()

        # Select the task once at start time
        self._active_task = (
            self._true_task if self._predicate() else self._false_task
        )

        # Start the chosen task
        self._active_task.start()

    def update(self, dt: float) -> None:
        if self._state is not AnimationState.RUNNING:
            return

        if not self._active_task:
            return

        self._active_task.update(dt)
        self._execute_callbacks(ScheduleType.ON_UPDATE)

        if self._active_task._state in (
            AnimationState.FINISHED,
            AnimationState.ABORTED,
        ):
            self.finish()

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        if (
            self._active_task
            and self._active_task._state == AnimationState.RUNNING
        ):
            self._active_task.abort()

        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        self._active_task = None
        super().kill()


class LoopTask(TaskBase):
    """
    Repeats a child task a fixed number of times.

    Before each iteration, the child task is cloned (deep-copied by default)
    to ensure it starts fresh. This is especially important for container
    tasks such as TaskSequence or TaskParallel, which maintain internal state.

    The LoopTask finishes only after all iterations complete. If the child
    task aborts, the loop still continues to the next iteration.

    Examples
    --------
    Looping a simple task:

        loop = LoopTask(
            Task(lambda: print("Tick"), interval=0.5, times=1),
            times=5,
        )
        group.add(loop)

    Looping a sequence:

        seq = TaskSequence(
            Animation(sprite, x=200, duration=1.0),
            Animation(sprite, x=100, duration=1.0),
        )

        loop = LoopTask(seq, times=3)
        group.add(loop)

    Notes
    -----
    - Each iteration receives a fresh copy of the original task.
    - The loop continues even if an iteration aborts.
    - Override clone_task() if deepcopy is not appropriate.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self, task: TaskBase, times: int) -> None:
        if times <= 0:
            raise ValueError("times must be a positive integer (>= 1)")

        super().__init__()
        self._original_task = task
        self._total_loops = times
        self._current_loop = 0
        self._active_task: TaskBase | None = None

    def clone_task(self) -> TaskBase:
        """Override this if deepcopy is not appropriate for a task type."""
        return deepcopy(self._original_task)

    def start(self) -> None:
        super().start()
        self._start_next_loop()

    def _start_next_loop(self) -> None:
        if self._current_loop >= self._total_loops:
            self.finish()
            return

        self._current_loop += 1
        self._active_task = self.clone_task()
        self._active_task.start()

    def update(self, dt: float) -> None:
        if self._state is not AnimationState.RUNNING:
            return
        if not self._active_task:
            return

        self._active_task.update(dt)
        self._execute_callbacks(ScheduleType.ON_UPDATE)

        if self._active_task._state in (
            AnimationState.FINISHED,
            AnimationState.ABORTED,
        ):
            self._start_next_loop()

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        if (
            self._active_task
            and self._active_task._state == AnimationState.RUNNING
        ):
            self._active_task.abort()

        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        self._active_task = None
        super().kill()


class RetryTask(TaskBase):
    """
    Retries a child task up to `max_attempts` times if it aborts.

    The child task is cloned before each attempt to ensure a clean reset.
    If the child task finishes normally, the RetryTask finishes successfully.
    If all attempts abort, the RetryTask aborts.

    This is useful for tasks that may fail due to temporary conditions
    (e.g., pathfinding, network checks, resource availability).

    Examples
    --------
    Retrying a failing task:

        def flaky():
            if random.random() < 0.7:
                raise AbortTask()
            print("Success!")

        retry = RetryTask(Task(flaky, interval=0.1, times=1), max_attempts=5)
        group.add(retry)

    Using inside a sequence:

        seq = TaskSequence(
            RetryTask(Animation(sprite, x=200, duration=1.0), max_attempts=3),
            Task(lambda: print("Move succeeded or gave up")),
        )
        group.add(seq)

    Notes
    -----
    - A successful finish ends the RetryTask immediately.
    - An aborted attempt triggers another attempt until max_attempts is reached.
    - Override clone_task() if deepcopy is not appropriate.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self, task: TaskBase, max_attempts: int) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts must be >= 1")

        super().__init__()
        self._original_task = task
        self._max_attempts = max_attempts
        self._current_attempt = 0
        self._active_task: TaskBase | None = None

    def clone_task(self) -> TaskBase:
        return self._original_task

    def start(self) -> None:
        super().start()
        self._run_attempt()

    def _run_attempt(self) -> None:
        if self._current_attempt >= self._max_attempts:
            self.abort()
            return

        self._current_attempt += 1
        self._active_task = self.clone_task()
        self._active_task.start()

    def update(self, dt: float) -> None:
        if self._state is not AnimationState.RUNNING or not self._active_task:
            return

        self._active_task.update(dt)
        self._execute_callbacks(ScheduleType.ON_UPDATE)

        if self._active_task._state is AnimationState.FINISHED:
            self.finish()
        elif self._active_task._state is AnimationState.ABORTED:
            self._run_attempt()

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        if (
            self._active_task
            and self._active_task._state is AnimationState.RUNNING
        ):
            self._active_task.abort()

        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        self._active_task = None
        super().kill()


class RaceTask(TaskBase):
    """
    Runs multiple tasks simultaneously and finishes as soon as any one of them
    reaches a terminal state (FINISHED or ABORTED).

    The first task to finish becomes the "winner". All other running tasks are
    immediately aborted. The RaceTask adopts the winner's state: if the winner
    finished normally, the RaceTask finishes; if the winner aborted, the
    RaceTask aborts.

    This is useful for timeouts, fallback behaviors, or "whichever finishes
    first" logic.

    Examples
    --------
    Timeout behavior:

        race = RaceTask(
            Animation(sprite, x=200, duration=3.0),
            DelayTask(1.0),  # timeout after 1 second
        )
        group.add(race)

    First animation to finish:

        race = RaceTask(
            Animation(sprite, x=200, duration=1.0),
            Animation(sprite, y=100, duration=0.5),  # finishes first
        )
        group.add(race)

    Using inside a sequence:

        seq = TaskSequence(
            RaceTask(
                Animation(sprite, x=200, duration=2.0),
                Task(lambda: print("User clicked"), interval=0.1, times=-1),
            ),
            Task(lambda: print("Race ended")),
        )
        group.add(seq)

    Notes
    -----
    - All tasks start simultaneously.
    - The first task to finish or abort determines the outcome.
    - All other tasks are aborted immediately.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self, *tasks: TaskBase) -> None:
        super().__init__()
        self._tasks = list(tasks)
        self._winner: TaskBase | None = None

    def start(self) -> None:
        super().start()
        for task in self._tasks:
            task.start()

    def update(self, dt: float) -> None:
        if self._state is not AnimationState.RUNNING:
            return

        for task in self._tasks:
            if task._state is AnimationState.RUNNING:
                task.update(dt)

        self._execute_callbacks(ScheduleType.ON_UPDATE)

        for task in self._tasks:
            if task._state in (
                AnimationState.FINISHED,
                AnimationState.ABORTED,
            ):
                self._winner = task
                self._end_race(task._state)
                return

    def _end_race(self, final_state: AnimationState) -> None:
        for task in self._tasks:
            if (
                task is not self._winner
                and task._state != AnimationState.ABORTED
            ):
                task.abort()

        if final_state is AnimationState.FINISHED:
            self.finish()
        else:
            self.abort()

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return
        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        self._tasks.clear()
        super().kill()


class DelayTask(TaskBase):
    """
    A simple task that waits for a specified duration before finishing.

    This is the cleanest way to insert pauses inside TaskSequence or
    TaskParallel. It behaves like a timer: once the elapsed time reaches
    the duration, the task finishes.

    Examples
    --------
    Basic delay:

        wait = DelayTask(1.0)  # wait 1 second
        group.add(wait)

    Using inside a sequence:

        seq = TaskSequence(
            Animation(sprite, x=200, duration=1.0),
            DelayTask(0.5),
            Animation(sprite, alpha=0, duration=0.5),
        )
        group.add(seq)

    Using in a race (timeout):

        race = RaceTask(
            Animation(sprite, x=200, duration=3.0),
            DelayTask(1.0),  # timeout after 1 second
        )
        group.add(race)

    Notes
    -----
    - Duration must be non-negative.
    - A duration of 0 finishes immediately on start().
    - Useful for pacing sequences or implementing timeouts.
    """

    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("Duration must be non-negative")

        super().__init__()
        self._duration = duration
        self._elapsed: float = 0.0
        self._state = AnimationState.NOT_STARTED

    def start(self) -> None:
        super().start()

        # If duration is zero, finish immediately
        if self._duration == 0.0 and self._state is AnimationState.RUNNING:
            self.finish()

    def update(self, dt: float) -> None:
        if self._state is not AnimationState.RUNNING:
            return

        self._elapsed += dt
        self._execute_callbacks(ScheduleType.ON_UPDATE)

        if self._elapsed >= self._duration:
            self.finish()

    def finish(self) -> None:
        if self._state is AnimationState.FINISHED:
            return

        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_FINISH)
        self.kill()

    def abort(self) -> None:
        self._state = AnimationState.ABORTED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self.kill()

    def kill(self) -> None:
        if self._state not in (
            AnimationState.FINISHED,
            AnimationState.ABORTED,
        ):
            self._state = AnimationState.ABORTED
        super().kill()
