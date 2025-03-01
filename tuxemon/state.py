# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import inspect
import logging
import os.path
import sys
import warnings
from abc import ABCMeta
from collections.abc import Callable, Generator, Mapping, Sequence
from importlib import import_module
from typing import Any, Optional, TypeVar, Union, overload

import pygame
from pygame.rect import Rect

from tuxemon import graphics, prepare
from tuxemon.animation import Animation, Task, remove_animations_of
from tuxemon.constants import paths
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.sprite import Sprite, SpriteGroup

logger = logging.getLogger(__name__)

StateType = TypeVar("StateType", bound="State")


class State:
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

    __metaclass__ = ABCMeta

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
        self.animations = pygame.sprite.Group()

        # All sprites that draw on the screen
        self.sprites: SpriteGroup[Sprite] = SpriteGroup()

        # TODO: fix local session
        self.client = local_session.client
        self._hooks: dict[str, list[Callable[..., None]]] = {}

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
        self.trigger_hook("update", time_delta)

    def draw(self, surface: pygame.surface.Surface) -> None:
        """
        Render the state to the surface passed. Must be overloaded in children.

        Do not change the state of any game entities. Every draw should be the
        same for a given game time. Any game changes should be done during
        update.

        Parameters:
            surface: Surface to be rendered onto.

        """
        self.trigger_hook("draw", surface)

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
        self.trigger_hook("resume")

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
        self.trigger_hook("pause")

    def shutdown(self) -> None:
        """
        Called when state is removed from stack and will be destroyed.

        This will be called:
        * after update when state is popped

        Make sure to release any references to objects that may cause
        cyclical dependencies.
        """
        self.trigger_hook("shutdown")

    def register_hook(
        self, hook_name: str, callback: Callable[..., None]
    ) -> None:
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def unregister_hook(
        self, hook_name: str, callback: Callable[..., None]
    ) -> None:
        if hook_name in self._hooks:
            try:
                self._hooks[hook_name].remove(callback)
            except ValueError:
                pass

    def trigger_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> None:
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                callback(*args, **kwargs)


class StateManager:
    """
    Allows game states to be managed like a queue.

    Parameters:
        package: Name of package to search for states.
        on_state_change: Optional callback to be executed when top state
            changes.

    """

    def __init__(
        self,
        package: str,
        on_state_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self.package = package
        self._state_queue: list[tuple[str, Mapping[str, Any]]] = []
        self._state_stack: list[State] = []
        self._state_dict: dict[str, type[State]] = {}
        self._resume_set: set[State] = set()
        self._global_hooks: dict[str, list[Callable[..., None]]] = {}
        if on_state_change:
            self.register_global_hook("on_state_change", on_state_change)
        self.register_global_hook("pre_state_update", lambda time_delta: None)
        self.register_global_hook("post_state_update", lambda time_delta: None)

    def register_global_hook(
        self, hook_name: str, callback: Callable[..., None]
    ) -> None:
        """
        Registers a callback function for a specific hook name.

        Parameters:
            hook_name: The name of the hook.
            callback: The callback function to register.
        """
        if not isinstance(hook_name, str) or not hook_name:
            raise ValueError(f"Hook '{hook_name}' must be a non-empty string")
        if not callable(callback):
            raise ValueError("Callback must be a callable function")
        if hook_name not in self._global_hooks:
            self._global_hooks[hook_name] = []
        self._global_hooks[hook_name].append(callback)

    def unregister_global_hook(
        self, hook_name: str, callback: Callable[..., None]
    ) -> None:
        """
        Unregisters a previously registered callback function for a
        specific hook name.

        Parameters:
            hook_name: The name of the hook.
            callback: The callback function to unregister.
        """
        if hook_name not in self._global_hooks:
            raise ValueError(f"Hook '{hook_name}' not found")
        try:
            self._global_hooks[hook_name].remove(callback)
        except ValueError:
            raise ValueError("Callback not found for hook")

    def trigger_global_hook(
        self, hook_name: str, *args: Any, **kwargs: Any
    ) -> None:
        """
        Triggers all registered callback functions for a specific hook
        name, passing in any additional arguments.

        Parameters:
            hook_name: The name of the hook.
            *args: Additional positional arguments to pass to the callbacks.
            **kwargs: Additional keyword arguments to pass to the callbacks.
        """
        if hook_name not in self._global_hooks:
            raise ValueError(f"Hook name '{hook_name}' not found")
        for callback in self._global_hooks[hook_name]:
            callback(*args, **kwargs)

    def is_hook_registered(self, hook_name: str) -> bool:
        """
        Checks if a hook with the given name is registered.
        """
        return hook_name in self._global_hooks

    def debug_hooks(self) -> None:
        """
        Prints out all registered hooks and their callback functions for
        debugging purposes.
        """
        for hook_name, callbacks in self._global_hooks.items():
            logger.debug(f"Hook: {hook_name}")
            for i, callback in enumerate(callbacks):
                logger.debug(f"  Callback {i+1}: {callback.__name__}")

    def auto_state_discovery(self) -> None:
        """
        Scan a folder, load states found in it, and register them.

        TODO: this functionality duplicates the plugin code.

        """
        state_folder = os.path.join(paths.LIBDIR, *self.package.split(".")[1:])
        exclude_endings = (".py", ".pyc", ".pyo", "__pycache__")
        logger.debug(f"loading game states from {state_folder}")
        for folder in os.listdir(state_folder):
            if any(folder.endswith(end) for end in exclude_endings):
                continue
            for state in self.collect_states_from_path(folder):
                self.register_state(state)

    def register_state(self, state: type[State]) -> None:
        """
        Add a state class.

        Parameters:
            state: The state to add.

        """
        name = state.__name__
        logger.debug(f"loading state: {name}")
        self._state_dict[name] = state

    def _instance(self, state_name: str, **kwargs: Any) -> State:
        """
        Create new instance of State. Builder patter, WIP.

        Parameters:
            state_name: Name of state to create.

        """
        try:
            state = self._state_dict[state_name]
        except KeyError:
            raise RuntimeError(f"Cannot find state: {state_name}")
        return state(**kwargs) if kwargs else state()

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
        folder: str,
    ) -> Generator[type[State], None, None]:
        """
        Load states from disk, but do not register it.

        Parameters:
            folder: Folder to load from.

        Yields:
            Each game state class.

        """
        try:
            import_name = self.package + "." + folder
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
            logger.debug("removing %s from resume set", state.name)
            self._resume_set.remove(state)
            state.resume()

    def query_all_states(self) -> Mapping[str, type[State]]:
        """
        Return a dictionary of all loaded states.

        Keys are state names, values are State classes.

        Returns:
            Dictionary of all loaded states.

        """
        return self._state_dict.copy()

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
        logger.debug("queue state: %s", state_name)
        self._state_queue.append((state_name, kwargs))

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
        # handle situation where there is a queued state
        if self._state_queue:
            state_name, kwargs = self._state_queue.pop(0)
            self.replace_state(state_name, **kwargs)
            logger.debug("pop state, using queue instead: %s", state_name)
            return

        # raise error if stack is empty
        if not self._state_stack:
            raise RuntimeError("Attempted to pop state when stack was empty.")

        # pop the top state
        if state is None:
            state = self._state_stack[0]

        try:
            index = self._state_stack.index(state)
        except IndexError:
            raise RuntimeError(
                "Attempted to pop state when state was not active.",
            )

        if index == 0:
            logger.debug("pop state: %s", state.name)
            self._state_stack.pop(0)
            self._check_resume(state)
            state.pause()
            state.shutdown()
            if self._state_stack:
                self._resume_set.add(self._state_stack[0])
            if self.is_hook_registered("on_state_change"):
                self.trigger_global_hook("on_state_change")
        else:
            logger.debug("pop-remove state: %s", state.name)
            self._state_stack.remove(state)

    def remove_state(self, state: State) -> None:
        """
        Remove state by passing a reference to it

        Parameters:
            state: State to remove

        """
        try:
            index = self._state_stack.index(state)
        except IndexError:
            logger.critical(
                "Attempted to remove state which is not in the stack",
            )
            raise RuntimeError

        if index == 0:
            logger.debug("remove-pop state: %s", state.name)
            self.pop_state()
        else:
            logger.debug("remove state: %s", state.name)
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
        logger.debug("push state: %s", state_name)
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
        logger.debug("replace state: %s", state_name)
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
