# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from math import cos, pi, sin, sqrt
from typing import Any, Optional, Union, cast
from weakref import ref

from pygame.rect import Rect
from pygame.sprite import Group, Sprite

__all__ = ("Task", "Animation", "remove_animations_of")


ScheduledFunction = Callable[[], Any]

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


def remove_animations_of(
    target: object, group: Group[Union[Task, Animation]]
) -> None:
    """
    Removes animations associated with a given target.

    Parameters:
        target: The object whose animations should be removed.
        group: A Pygame group containing `Animation` instances.
    """
    animations = {ani for ani in group if isinstance(ani, Animation)}
    to_remove = [
        ani
        for ani in animations
        if any(td.target_ref() == target for td in ani.targets)
    ]
    if not to_remove:
        logger.debug(f"No animations found for target: {target}")
    group.remove(*to_remove)


class TaskBase(Sprite):
    _valid_schedules: Sequence[ScheduleType] = []

    def __init__(self) -> None:
        super().__init__()
        self._callbacks: defaultdict[
            ScheduleType,
            list[tuple[ScheduledFunction, tuple[Any, ...], dict[str, Any]]],
        ] = defaultdict(list)

    def schedule(
        self,
        func: ScheduledFunction,
        when: Optional[ScheduleType] = None,
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
        if when is None:
            when = self._valid_schedules[0]

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
                func(*args, **kwargs)


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
            raise ValueError("callback must be callable")

        if interval < 0:
            raise ValueError("interval must be non negative")

        if times < -1 or times == 0:
            raise ValueError(
                "times must be -1 for infinite loops, or a positive integer (>= 1)"
            )

        super().__init__()
        self._interval = interval
        self._loops = times
        self._duration: float = 0
        self._chain: list[Task] = []
        self._state = AnimationState.RUNNING
        self.schedule(callback, ScheduleType.ON_INTERVAL)

    def chain(
        self,
        callback: ScheduledFunction,
        interval: float = 0,
        times: int = 1,
    ) -> None:
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
        self.chain_task(Task(callback, interval, times))

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
                if self._loops == 0:
                    self.finish()
                else:
                    self._execute_callbacks(ScheduleType.ON_INTERVAL)
            elif self._loops == -1:
                self._execute_callbacks(ScheduleType.ON_INTERVAL)

    def finish(self) -> None:
        """Force task to finish, while executing callbacks."""
        if self._state is AnimationState.RUNNING:
            self._state = AnimationState.FINISHED
            self._execute_callbacks(ScheduleType.ON_INTERVAL)
            self._execute_callbacks(ScheduleType.ON_FINISH)
            self._execute_chain()
            self._cleanup()
        else:
            logger.debug(
                "Task already finished or not running, cannot finish again."
            )

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
            self._duration = 0

    def abort(self) -> None:
        """Force task to finish, without executing 'on interval' callbacks."""
        if self._state is AnimationState.FINISHED:
            return

        self._state = AnimationState.FINISHED
        self._execute_callbacks(ScheduleType.ON_ABORT)
        self._cleanup()

    def _cleanup(self) -> None:
        self._chain = []
        self.kill()

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
        duration: Optional[float] = None,
        transition: Union[str, Callable[[float], float], None] = None,
        initial: Union[float, Callable[[], float], None] = None,
        relative: bool = False,
        yoyo: bool = False,
        yoyo_loops: int = -1,
        **kwargs: Any,
    ) -> None:
        super().__init__()

        self.targets: list[AnimatedTargetData] = []
        self._targets: Sequence[ref[object]] = []

        self.delay = delay
        self._state = AnimationState.NOT_STARTED
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
        self, transition: Union[str, Callable[[float], float], None] = None
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

    def update(self, time_delta: float) -> None:

        if self._state in (AnimationState.FINISHED, AnimationState.ABORTED):
            return

        if self._state is not AnimationState.RUNNING:
            return

        if self._duration == 0:
            self.finish()
            return

        self._elapsed += time_delta

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

    def finish(self) -> None:
        if self._state is not AnimationState.RUNNING:
            return

        for target_data in self.targets:
            target = target_data.target_ref()
            if target:
                for name, prop_data in target_data.properties.items():
                    self._set_value(target, name, prop_data.final)

        self._execute_callbacks(ScheduleType.ON_UPDATE)

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
            self._is_yoyo_reverse = not self._is_yoyo_reverse
            for target_data in self.targets:
                for prop_data in target_data.properties.values():
                    prop_data.initial, prop_data.final = (
                        prop_data.final,
                        prop_data.initial,
                    )
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


class AnimationTransition:
    """
    Collection of animation functions to be used with the Animation object.

    Easing Functions ported to Kivy from the Clutter Project
    http://www.clutter-project.org/docs/clutter/stable/ClutterAlpha.html

    The `progress` parameter in each animation function is in the range 0-1.
    """

    @staticmethod
    def linear(progress: float) -> float:
        return progress

    @staticmethod
    def in_quad(progress: float) -> float:
        return progress * progress

    @staticmethod
    def out_quad(progress: float) -> float:
        return -1.0 * progress * (progress - 2.0)

    @staticmethod
    def in_out_quad(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    @staticmethod
    def in_cubic(progress: float) -> float:
        return progress * progress * progress

    @staticmethod
    def out_cubic(progress: float) -> float:
        p = progress - 1.0
        return p * p * p + 1.0

    @staticmethod
    def in_out_cubic(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    @staticmethod
    def in_quart(progress: float) -> float:
        return progress * progress * progress * progress

    @staticmethod
    def out_quart(progress: float) -> float:
        p = progress - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    @staticmethod
    def in_out_quart(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    @staticmethod
    def in_quint(progress: float) -> float:
        return progress * progress * progress * progress * progress

    @staticmethod
    def out_quint(progress: float) -> float:
        p = progress - 1.0
        return p * p * p * p * p + 1.0

    @staticmethod
    def in_out_quint(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    @staticmethod
    def in_sine(progress: float) -> float:
        return -1.0 * cos(progress * (pi / 2.0)) + 1.0

    @staticmethod
    def out_sine(progress: float) -> float:
        return sin(progress * (pi / 2.0))

    @staticmethod
    def in_out_sine(progress: float) -> float:
        return -0.5 * (cos(pi * progress) - 1.0)

    @staticmethod
    def in_expo(progress: float) -> float:
        if progress == 0:
            return 0.0
        value = pow(2, 10 * (progress - 1.0))
        return float(value)

    @staticmethod
    def out_expo(progress: float) -> float:
        if progress == 1.0:
            return 1.0
        value = -pow(2, -10 * progress) + 1.0
        return float(value)

    @staticmethod
    def in_out_expo(progress: float) -> float:
        if progress == 0:
            return 0.0
        if progress == 1.0:
            return 1.0
        p = progress * 2
        if p < 1:
            value = 0.5 * pow(2, 10 * (p - 1.0))
            return float(value)
        p -= 1.0
        value = 0.5 * (-pow(2, -10 * p) + 2.0)
        return float(value)

    @staticmethod
    def in_circ(progress: float) -> float:
        return -1.0 * (sqrt(1.0 - progress * progress) - 1.0)

    @staticmethod
    def out_circ(progress: float) -> float:
        p = progress - 1.0
        return sqrt(1.0 - p * p)

    @staticmethod
    def in_out_circ(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    @staticmethod
    def in_elastic(progress: float) -> float:
        p = 0.3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        q -= 1.0
        value = -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))
        return float(value)

    @staticmethod
    def out_elastic(progress: float) -> float:
        p = 0.3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        value = pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0
        return float(value)

    @staticmethod
    def in_out_elastic(progress: float) -> float:
        p = 0.3 * 1.5
        s = p / 4.0
        q = progress * 2
        if q == 2:
            return 1.0
        if q < 1:
            q -= 1.0
            value = -0.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 * pi) / p))
            return float(value)
        else:
            q -= 1.0
            value = pow(2, -10 * q) * sin((q - s) * (2.0 * pi) / p) * 0.5 + 1.0
            return float(value)

    @staticmethod
    def in_back(progress: float) -> float:
        return progress * progress * ((1.70158 + 1.0) * progress - 1.70158)

    @staticmethod
    def out_back(progress: float) -> float:
        p = progress - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    @staticmethod
    def in_out_back(progress: float) -> float:
        p = progress * 2.0
        s = 1.70158 * 1.525
        if p < 1:
            return 0.5 * (p * p * ((s + 1.0) * p - s))
        p -= 2.0
        return 0.5 * (p * p * ((s + 1.0) * p + s) + 2.0)

    @staticmethod
    def _out_bounce_internal(t: float, d: float) -> float:
        p = t / d
        if p < (1.0 / 2.75):
            return 7.5625 * p * p
        elif p < (2.0 / 2.75):
            p -= 1.5 / 2.75
            return 7.5625 * p * p + 0.75
        elif p < (2.5 / 2.75):
            p -= 2.25 / 2.75
            return 7.5625 * p * p + 0.9375
        else:
            p -= 2.625 / 2.75
            return 7.5625 * p * p + 0.984375

    @staticmethod
    def _in_bounce_internal(t: float, d: float) -> float:
        return 1.0 - AnimationTransition._out_bounce_internal(d - t, d)

    @staticmethod
    def in_bounce(progress: float) -> float:
        return AnimationTransition._in_bounce_internal(progress, 1.0)

    @staticmethod
    def out_bounce(progress: float) -> float:
        return AnimationTransition._out_bounce_internal(progress, 1.0)

    @staticmethod
    def in_out_bounce(progress: float) -> float:
        p = progress * 2.0
        if p < 1.0:
            return AnimationTransition._in_bounce_internal(p, 1.0) * 0.5
        return (
            AnimationTransition._out_bounce_internal(p - 1.0, 1.0) * 0.5 + 0.5
        )
