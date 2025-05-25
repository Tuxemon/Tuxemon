# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import inspect
import logging
import random
import sys
import warnings
from abc import ABC
from collections.abc import Callable, Generator, Mapping, Sequence
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Optional, TypeVar, Union, overload

from pygame.rect import Rect
from pygame.sprite import Group
from pygame.surface import Surface

from tuxemon import graphics, prepare
from tuxemon.animation import Animation, Task, remove_animations_of
from tuxemon.constants import paths
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.sprite import Sprite, SpriteGroup

logger = logging.getLogger(__name__)

StateType = TypeVar("StateType", bound="State")


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
        *args: Any,
        callback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Task:
        """
        Create a task for this state.

        Tasks are processed even while state is inactive.
        If you want to pass positional arguments, use functools.partial.

        Parameters:
            args: Function to be called.
            callback: Function to be called when the task finishes.
            kwargs: Keyword parameters passed to the task.

        Returns:
            The created task.
        """
        if not args:
            raise ValueError("Must provide a function to be called")

        task = Task(*args, **kwargs)
        self.animations.add(task)

        if callback is not None:
            if not callable(callback):
                raise ValueError("Callback must be a callable function")
            task.schedule(callback, "on finish")

        return task

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
            partial(self.schedule_callback, _frequency, callback), time
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


class StateManager:
    """
    Allows game states to be managed like a queue.

    Parameters:
        package: Name of package to search for states.
        hook: Manages hooks for executing custom logic during state changes.
        repository: Repository for accessing state instances.
        on_state_change: Optional callback to be executed when top state
            changes.
    """

    def __init__(
        self,
        package: str,
        hook: HookManager,
        repository: StateRepository,
        on_state_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self.package = package
        self.hook_manager = hook
        self.state_repository = repository
        self._state_queue: list[tuple[str, Mapping[str, Any]]] = []
        self._state_stack: list[State] = []
        self._resume_set: set[State] = set()
        if on_state_change:
            self.register_global_hook("on_state_change", on_state_change)
        self.register_global_hook("pre_state_update", lambda time_delta: None)
        self.register_global_hook("post_state_update", lambda time_delta: None)

    def register_global_hook(
        self, hook_name: str, callback: Callable[..., None], priority: int = 0
    ) -> None:
        self.hook_manager.register_hook(hook_name, callback, priority)

    def unregister_global_hook(
        self, hook_name: str, callback: Callable[..., None]
    ) -> None:
        self.hook_manager.unregister_hook(hook_name, callback)

    def trigger_global_hook(
        self, hook_name: str, *args: Any, **kwargs: Any
    ) -> None:
        self.hook_manager.trigger_hook(hook_name, *args, **kwargs)

    def is_hook_registered(self, hook_name: str) -> bool:
        return self.hook_manager.is_hook_registered(hook_name)

    def auto_state_discovery(self) -> None:
        """
        Scan a folder, load states found in it, and register them.

        TODO: this functionality duplicates the plugin code.
        """
        state_folder = paths.LIBDIR / Path(*self.package.split(".")[1:])
        exclude_endings = {".py", ".pyc", ".pyo"}
        exclude_names = {"__pycache__"}

        logger.debug(f"Loading game states from {state_folder}")

        for folder in state_folder.iterdir():
            if (
                folder.is_dir()
                and not any(
                    folder.name.endswith(end) for end in exclude_endings
                )
                and folder.name not in exclude_names
            ):
                for state in self.collect_states_from_path(folder):
                    self.register_state(state)

    def register_state(self, state: type[State]) -> None:
        """Add a state class."""
        name = state.__name__
        logger.debug(f"loading state: {name}")
        self.state_repository.add_state(state)

    def _instance(self, state_name: str, **kwargs: Any) -> State:
        """Create new instance of State."""
        try:
            state_cls = self.state_repository.get_state(state_name)
        except KeyError:
            raise RuntimeError(f"Cannot find state: {state_name}")

        builder = StateBuilder(state_cls)
        for key, value in kwargs.items():
            builder.add_attribute(key, value)
        return builder.build()

    @staticmethod
    def collect_states_from_module(
        import_name: str,
    ) -> Generator[type[State], None, None]:
        """
        Given a module, return all classes in it that are a game state.

        Abstract Base Classes, those whose metaclass is abc.ABCMeta, will
        not be included in the state dictionary.

        Parameters:
            import_name: Name of module

        Yields:
            Each game state class.
        """
        classes = inspect.getmembers(sys.modules[import_name], inspect.isclass)

        for c in (i[1] for i in classes):
            if issubclass(c, State):
                yield c

    def collect_states_from_path(
        self,
        folder: Path,
    ) -> Generator[type[State], None, None]:
        """
        Load states from disk, but do not register it.

        Parameters:
            folder: Folder to load from.

        Yields:
            Each game state class.
        """
        try:
            import_name = self.package + "." + folder.name
            import_module(import_name)
            yield from self.collect_states_from_module(import_name)
        except Exception as e:
            template = "{} failed to load or is not a valid game package"
            logger.error(e)
            logger.error(template.format(folder))
            raise

    def update(self, time_delta: float) -> None:
        """
        Run update on all active states, which doing some internal housekeeping.

        WIP. This may change at some point, especially handling of paused
        states.

        Parameters:
            time_delta: Amount of time passed since last frame.
        """
        logger.debug("updating states")
        self.trigger_global_hook("pre_state_update", time_delta)
        for state in self.active_states:
            self._check_resume(state)
            state.update(time_delta)
        self.trigger_global_hook("post_state_update", time_delta)

    def _check_resume(self, state: State) -> None:
        """
        Call resume on states that are in the resume set.

        Typically states will resume right before an update, but if an update
        has not been called before an update, then the resume will be missed.

        This is used to enforce the symmetry between resume/pause calls.

        Parameters:
            state: State to check for resume
        """
        if state in self._resume_set:
            logger.debug(f"removing {state.name} from resume set")
            self._resume_set.remove(state)
            state.resume()

    def query_all_states(self) -> Mapping[str, type[State]]:
        """Return a dictionary of all loaded states."""
        return self.state_repository.all_states()

    def queue_state(self, state_name: str, **kwargs: Any) -> None:
        """
        Queue a state to be pushed after the top state is popped or replaced.

        Use this to chain execution of states, without causing a
        state to get instanced before it is on top of the stack.

        Parameters:
            state_name: Name of state to start.
            kwargs: Arguments to pass to the ``__init__`` method of the
                new state.
        """
        logger.debug(f"queue state: {state_name}")
        self._state_queue.append((state_name, kwargs))

    def pop_current_state(self) -> None:
        """Pop the current state from the stack."""
        if not self._state_stack:
            raise RuntimeError("Attempted to pop state when stack was empty.")

        state = self._state_stack.pop(0)
        logger.debug(f"Pop state: {state.name}")

        self._check_resume(state)
        state.pause()
        state.shutdown()

        if self._state_stack:
            self._resume_set.add(self._state_stack[0])

        if self.is_hook_registered("on_state_change"):
            self.trigger_global_hook("on_state_change")

    def handle_queued_state(self) -> None:
        """Handle a queued state if one exists."""
        if self._state_queue:
            state_name, kwargs = self._state_queue.pop(0)
            self.replace_state(state_name, **kwargs)
            logger.debug(f"Pop state, using queue instead: {state_name}")

    def pop_state(self, state: Optional[State] = None) -> None:
        """
        Pop some state.

        The default state is the current one. The previously running state
        will resume, unless there is a queued state, then that state will be
        become the new current state, not the previous.

        Parameters:
            state: The state to remove from stack. Use None (or omit) for
                current state.
        """
        if self._state_queue:
            self.handle_queued_state()
            return

        if state is None:
            self.pop_current_state()
        else:
            index = self.find_state_in_stack(state)
            if index == 0:
                self.pop_current_state()
            else:
                logger.debug(f"Pop-remove state: {state.name}")
                self._state_stack.remove(state)

    def find_state_in_stack(self, state: State) -> int:
        """Find the state in the stack."""
        try:
            index = self._state_stack.index(state)
        except IndexError:
            logger.critical(
                "Attempted to remove state which is not in the stack",
            )
            raise RuntimeError
        return index

    def remove_state(self, state: State) -> None:
        """
        Remove state by passing a reference to it

        Parameters:
            state: State to remove
        """
        index = self.find_state_in_stack(state)
        if index == 0:
            logger.debug(f"remove-pop state: {state.name}")
            self.pop_state()
        else:
            logger.debug(f"remove state: {state.name}")
            self._state_stack.remove(state)
            state.shutdown()

    def remove_state_by_name(self, state_name: str) -> None:
        """
        Remove a state from the stack by its name.

        Parameters:
            state_name: The name of the state to remove.
        """

        try:
            for index, state in enumerate(self._state_stack):
                if state.name == state_name:
                    if index == 0:
                        self.pop_state()
                    else:
                        self._state_stack.remove(state)
                        state.shutdown()
                    return
        except IndexError:
            logger.critical(
                "Attempted to remove state which is not in the stack",
            )
            raise RuntimeError

        # If the state wasn't found, raise an error
        raise ValueError(f"State with name '{state_name}' not found")

    @overload
    def push_state(
        self, state_name: str, **kwargs: Optional[dict[str, Any]]
    ) -> State:
        pass

    @overload
    def push_state(
        self,
        state_name: StateType,
        **kwargs: Optional[dict[str, Any]],
    ) -> StateType:
        pass

    def push_state(
        self,
        state_name: Union[str, StateType],
        **kwargs: Optional[dict[str, Any]],
    ) -> State:
        """
        Pause currently running state and start new one.

        Parameters:
            state_name: Name of state to start.
            kwargs: Arguments to pass to the ``__init__`` method of the
                new state.

        Returns:
            Instanced state.
        """
        logger.debug(f"push state: {state_name}")
        previous = self.current_state
        if previous is not None:
            self._check_resume(previous)
            previous.pause()

        if isinstance(state_name, State):
            instance = state_name
        elif isinstance(state_name, str):
            instance = self._instance(state_name, **kwargs)
        else:
            warnings.warn(
                "Calling push_state with Type[State] is deprecated, use an instantiated State instead",
                DeprecationWarning,
            )
            instance = state_name(**kwargs) if kwargs else state_name()

        self._resume_set.add(instance)
        self._state_stack.insert(0, instance)

        if self.is_hook_registered("on_state_change"):
            self.trigger_global_hook("on_state_change")

        return instance

    @overload
    def replace_state(
        self, state_name: str, **kwargs: Optional[dict[str, Any]]
    ) -> State:
        pass

    @overload
    def replace_state(
        self,
        state_name: StateType,
        **kwargs: Optional[dict[str, Any]],
    ) -> StateType:
        pass

    def replace_state(
        self,
        state_name: Union[str, State],
        **kwargs: Optional[dict[str, Any]],
    ) -> State:
        """
        Replace the currently running state with a new one.

        This is essentially, just a ``push_state``, followed by
        ``pop_state(running_state)``.
        This cannot be used to replace states in the middle of the stack.

        Parameters:
            state_name: Name of state to start.
            kwargs: Arguments to pass to the ``__init__`` method of the
                new state.

        Returns:
            Instanced state.
        """
        logger.debug(f"replace state: {state_name}")
        # raise error if stack is empty
        if not self._state_stack:
            raise RuntimeError(
                "Attempted to replace state when stack was empty."
            )

        previous = self._state_stack[0]
        instance = self.push_state(state_name, **kwargs)
        self.remove_state(previous)
        return instance

    def push_state_with_timeout(
        self, state_name: Union[str, StateType], updates: int = 1
    ) -> None:
        """
        Push a state onto the stack and schedule it to be destroyed after
        a specified number of updates.

        Parameters:
            state_name: The state to push onto the stack.
            updates: The number of updates after which the state will be
                destroyed.
        """
        state = self.push_state(state_name)
        state.task(lambda: self.pop_state(state), times=updates)

    @property
    def current_state(self) -> Optional[State]:
        """
        Return the currently running state, if any.

        Returns:
            Currently running state.
        """
        try:
            return self._state_stack[0]
        except IndexError:
            return None

    @property
    def active_states(self) -> Sequence[State]:
        """
        Sequence of states that are active.

        Returns:
            List of active states.
        """
        return self._state_stack[:]

    @property
    def queued_states(self) -> Sequence[tuple[str, Mapping[str, Any]]]:
        """
        Sequence of states that are queued.

        Returns:
            List of queued states
        """
        return self._state_queue[:]

    @overload
    def get_state_by_name(self, state_name: str) -> State:
        pass

    @overload
    def get_state_by_name(
        self,
        state_name: type[StateType],
    ) -> StateType:
        pass

    def get_state_by_name(
        self,
        state_name: Union[str, type[State]],
    ) -> State:
        """
        Query the state stack for a state by the name supplied.

        Parameters:
            state_name: Name of a state.

        Returns:
            State with that name, if one exist. ``None`` otherwise.
        """
        for state in self.active_states:
            if (
                state.__class__.__name__ == state_name
                or state.__class__ == state_name
            ):
                return state

        raise ValueError(f"Missing state {state_name}")

    def get_queued_state_by_name(
        self,
        state_name: str,
    ) -> tuple[str, Mapping[str, Any]]:
        """
        Query the queued state stack for a state by the name supplied.

        Parameters:
            state_name: Name of a state.

        Returns:
            State with that name, if one exist. ``None`` otherwise.
        """
        for queued_state in self._state_queue:
            if queued_state[0] == state_name:
                return queued_state

        raise ValueError(f"Missing queued state {state_name}")

    def get_active_state_names(self) -> Sequence[str]:
        """List of names of active states."""
        return [state.name for state in self._state_stack]


class StateRepository:
    def __init__(self) -> None:
        self._state_dict: dict[str, type[State]] = {}

    def add_state(self, state: type[State], strict: bool = False) -> None:
        """
        Adds a state to the repository.

        Parameters:
            state: The state class to register.
            strict: If True, raises an error if the state is already registered.
                Defaults to False.

        Raises:
            ValueError: If the state is already registered and strict is True.
        """
        name = state.__name__
        if name in self._state_dict:
            if strict:
                raise ValueError(f"State '{name}' is already registered.")
            else:
                logger.warning(
                    f"State '{name}' is already registered. Overwriting."
                )
        self._state_dict[name] = state

    def get_state(self, name: str) -> type[State]:
        """Retrieve a state by its name."""
        try:
            return self._state_dict[name]
        except KeyError:
            raise ValueError(f"State '{name}' is not registered.")

    def all_states(self) -> dict[str, type[State]]:
        """Retrieve all registered states."""
        return self._state_dict.copy()


class StateBuilder:
    def __init__(self, state_cls: type[State]) -> None:
        """
        Initializes the builder for a specific state class.

        Parameters:
            state_cls: The class of the state to be constructed.
        """
        self.state_cls = state_cls
        self.attributes: dict[str, Any] = {}

    def add_attribute(self, key: str, value: Any) -> StateBuilder:
        """
        Add an attribute or parameter to the state.

        Parameters:
            key: The name of the attribute.
            value: The value of the attribute.

        Returns:
            The builder instance (for method chaining).
        """
        self.attributes[key] = value
        return self

    def build(self) -> State:
        """
        Constructs the state instance with the specified attributes.

        Returns:
            An instance of the state class.
        """
        return self.state_cls(**self.attributes)


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
