# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from abc import ABC
from collections.abc import Callable
from functools import partial
from typing import Any, Optional, Union

from pygame.rect import Rect
from pygame.sprite import Group
from pygame.surface import Surface

from tuxemon import graphics, prepare
from tuxemon.animation import (
    Animation,
    ScheduledFunction,
    ScheduleType,
    Task,
    remove_animations_of,
)
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.sprite import Sprite, SpriteGroup

logger = logging.getLogger(__name__)


class State(ABC):
    """This is a prototype class for States.

    All states should inherit from it. No direct instances of this
    class should be created. Update must be overloaded in the child class.

    Overview of Methods:
     * resume        - Called each time state is updated for first time
     * update        - Called each frame while state is active
     * process_event - Called when there is a new input event
     * pause         - Called when state is no longer active
     * shutdown      - Called before state is destroyed
    """

    rect = Rect((0, 0), prepare.SCREEN_SIZE)
    transparent = False  # ignore all background/borders
    force_draw = False  # draw even if completely under another state

    def __init__(self) -> None:
        """
        Constructor

        Attributes:
            force_draw: If True, state will never be skipped in drawing phase.
            rect: Area of the screen will be drawn on.

        Important!  The state must be ready to be drawn after this is called.
        """
        self.start_time = 0.0
        self.current_time = 0.0

        # Only animations and tasks
        self.animations: Group[Union[Task, Animation]] = Group()

        # All sprites that draw on the screen
        self.sprites: SpriteGroup[Sprite] = SpriteGroup()

        # TODO: fix local session
        self.client = local_session.client

        self._scheduled_task: Optional[Task] = None

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def load_sprite(self, filename: str, **kwargs: Any) -> Sprite:
        """
        Load a sprite and add it to this state.

        Parameters:
            filename: Filename, relative to the resources folder.
            kwargs: Keyword arguments to pass to the Rect constructor. Can be
                any value used by Rect, or layer.

        Returns:
            Loaded sprite.
        """
        layer = kwargs.pop("layer", 0)
        sprite = graphics.load_sprite(filename, **kwargs)
        self.sprites.add(sprite, layer=layer)
        return sprite

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
        ani = Animation(*targets, **kwargs)
        self.animations.add(ani)
        return ani

    def task(
        self,
        func: ScheduledFunction,
        on_finish: Optional[ScheduledFunction] = None,
        on_update: Optional[ScheduledFunction] = None,
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
        self.animations.add(task)

        callbacks_to_schedule = {}
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

        return task

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

        def chain(index: int = 0) -> None:
            if index >= len(fns):
                return
            anim = fns[index]()
            anim.schedule(
                lambda: chain(index + 1), when=ScheduleType.ON_FINISH
            )

        self.task(lambda: chain(0), interval=start_delay)

    def remove_animations_of(self, target: Any) -> None:
        """
        Given and object, remove any animations that it is used with.

        Parameters:
            target: Object whose animations should be removed.
        """
        remove_animations_of(target, self.animations)

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """
        Handles player input events.

        This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one. Returning None
        signifies that this method has dealt with an event and wants it
        exclusively. Return the event and others can use it as well.

        You should return None if you have handled input here.

        Parameters:
            event: Player input event.

        Returns:
            ``None`` if the event should not be passed to the next
            handlers. Otherwise, return the input event.
        """
        return event

    def update(self, time_delta: float) -> None:
        """
        Time update function for state. Must be overloaded in children.

        Parameters:
            time_delta: Amount of time in fractional seconds since last update.
        """
        self.animations.update(time_delta)
        self.sprites.update(time_delta)
        self.trigger_hook("state_update", time_delta)

    def draw(self, surface: Surface) -> None:
        """
        Render the state to the surface passed. Must be overloaded in children.

        Do not change the state of any game entities. Every draw should be the
        same for a given game time. Any game changes should be done during
        update.

        Parameters:
            surface: Surface to be rendered onto.
        """
        self.trigger_hook("state_draw", surface)

    def resume(self) -> None:
        """
        Called before update when state is newly in focus.

        This will be called:
        * before next update
        * after a pop operation which causes this state to be in focus

        After being called, state will begin to receive player input.
        Could be called several times over lifetime of state.

        Example uses: starting music, open menu, starting animations,
        timers, etc.
        """
        self.trigger_hook("state_resume")

    def pause(self) -> None:
        """
        Called when state is pushed back in the stack, allowed to pause.

        This will be called:
        * after update when state is pushed back
        * before being shutdown

        After being called, state will no longer receive player input.
        Could be called several times over lifetime of state.

        Example uses: stopping music, sounds, fading out, making state
        graphics dim, etc.
        """
        self.trigger_hook("state_pause")

    def shutdown(self) -> None:
        """
        Called when state is removed from stack and will be destroyed.

        This will be called:
        * after update when state is popped

        Make sure to release any references to objects that may cause
        cyclical dependencies.
        """
        self.trigger_hook("state_shutdown")

    def stop_scheduled_callbacks(self) -> None:
        """Stops any further scheduled callbacks by killing the task."""
        if self._scheduled_task:
            self._scheduled_task.abort()
            self._scheduled_task = None

    def schedule_callback(
        self,
        frequency: float,
        callback: Callable[[], None],
        min_frequency: float = 0.5,
        max_frequency: float = 5,
    ) -> None:
        """
        Schedules a callback function to execute at randomized intervals.

        This utility method sets up repeated execution of a given callback
        by scheduling it within a dynamic time frame.

        - Stops scheduling if the frequency is set to zero.
        - Ensures the execution interval falls within the defined limits
            (`min_frequency` to `max_frequency`).
        - Introduces randomization to prevent predictable timing patterns.
        - Executes the callback function immediately after scheduling.

        Parameters:
            frequency: The base frequency that determines execution intervals.
            callback: The function to be executed at each scheduled interval.
            min_frequency: The minimum allowed execution delay. Defaults to 0.5.
            max_frequency: The maximum allowed execution delay. Defaults to 5.
        """
        if frequency == 0.0:
            return
        _frequency = min(max_frequency, max(min_frequency, frequency))
        time = (min_frequency + min_frequency * random.random()) * _frequency
        self._scheduled_task = self.task(
            partial(self.schedule_callback, _frequency, callback),
            interval=time,
        )
        callback()

    def register_hook(
        self, hook_name: str, callback: Callable[..., None], priority: int = 0
    ) -> None:
        self.client.hook_manager.register_hook(hook_name, callback, priority)

    def unregister_hook(
        self, hook_name: str, callback: Callable[..., None]
    ) -> None:
        if self.client.hook_manager.is_hook_registered(hook_name):
            self.client.hook_manager.unregister_hook(hook_name, callback)

    def trigger_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> None:
        if self.client.hook_manager.is_hook_registered(hook_name):
            self.client.hook_manager.trigger_hook(hook_name, *args, **kwargs)

    def replace_hooks(
        self, hook_name: str, hooks: list[tuple[int, Callable[..., None]]]
    ) -> None:
        if self.client.hook_manager.is_hook_registered(hook_name):
            self.client.hook_manager._hooks[hook_name] = hooks


class HookManager:
    def __init__(self) -> None:
        self._hooks: dict[str, list[tuple[int, Callable[..., None]]]] = {}

    def register_hook(
        self, name: str, callback: Callable[..., None], priority: int = 0
    ) -> None:
        """
        Registers a callback function for a specified hook.

        Parameters:
            name: The unique name of the hook (non-empty string).
            callback: A callable function for the hook.
            priority: Execution priority (default is 0).

        Raises:
            ValueError: If the name is empty or callback is not callable.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("Hook name must be a non-empty string.")
        if not callable(callback):
            raise ValueError("Callback must be callable.")

        if name not in self._hooks:
            self._hooks[name] = []
        self._hooks[name].append((priority, callback))
        self._hooks[name].sort(reverse=True, key=lambda hook: hook[0])

    def unregister_hook(
        self,
        name: str,
        callback: Callable[..., None],
        priority: Optional[int] = None,
    ) -> None:
        """
        Unregisters a callback function from a specified hook.

        Parameters:
            name: The unique name of the hook.
            callback: The callback function to remove.
            priority: The priority of the callback (optional).

        Raises:
            ValueError: If the hook does not exist.
        """
        if name not in self._hooks:
            raise ValueError(f"Hook '{name}' not found.")
        self._hooks[name] = [
            (p, cb)
            for p, cb in self._hooks[name]
            if cb != callback or (priority is not None and p != priority)
        ]
        if not self._hooks[name]:
            del self._hooks[name]

    def trigger_hook(self, name: str, *args: Any, **kwargs: Any) -> None:
        """
        Triggers all registered callback functions for a specific hook
        name, passing in any additional arguments.

        Parameters:
            hook_name: The name of the hook.
            *args: Additional positional arguments to pass to the callbacks.
            **kwargs: Additional keyword arguments to pass to the callbacks.
        """
        if name not in self._hooks:
            raise ValueError(f"Hook '{name}' is not registered.")
        for _, callback in self._hooks[name]:
            callback(*args, **kwargs)

    def debug_hooks(self) -> None:
        """Log all hooks and their priorities."""
        for name, callbacks in self._hooks.items():
            logger.debug(f"Hook: {name}")
            for priority, callback in callbacks:
                logger.debug(f"  Priority {priority}: {callback.__name__}")

    def reset_hooks(self) -> None:
        """Reset all hooks."""
        self._hooks.clear()

    def is_hook_registered(self, name: str) -> bool:
        """
        Checks if a hook with the given name is registered.
        """
        return name in self._hooks
