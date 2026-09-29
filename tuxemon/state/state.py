# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from abc import ABC
from collections.abc import Callable, Iterable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pygame.rect import Rect

from tuxemon.event.eventbus import Listener
from tuxemon.graphics import load_animated_sprite, load_sprite, load_surface
from tuxemon.sprite import Sprite, SpriteGroup
from tuxemon.state.animation_mixin import AnimationMixin
from tuxemon.state.render_mixin import RenderMixin

if TYPE_CHECKING:
    from pygame.surface import Surface

    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput

logger = logging.getLogger(__name__)


class State(AnimationMixin, RenderMixin, ABC):
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

    name: ClassVar[str] = "State"
    transparent = False  # ignore all background/borders
    force_draw = False  # draw even if completely under another state

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any) -> None:
        """
        Constructor

        Attributes:
            force_draw: If True, state will never be skipped in drawing phase.
            rect: Area of the screen will be drawn on.

        Important!  The state must be ready to be drawn after this is called.
        """
        super().__init__()
        self.start_time = 0.0
        self.current_time = 0.0

        # All sprites that draw on the screen
        self.sprites: SpriteGroup[Sprite] = SpriteGroup()

        self.client = client
        self.event_bus = client.event_bus
        self.rect = Rect((0, 0), self._get_resolution())

    def __init_subclass__(cls: type[State], **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Ensure subclass defines its own `name`
        if "name" not in cls.__dict__:
            logger.error(f"Missing 'name' in subclass: {cls.__name__}")
            raise TypeError(
                f"{cls.__name__} must define a class variable 'name'"
            )

        # Ensure subclass explicitly defines __init__(self, client, ...)
        init = cls.__dict__.get("__init__")
        if init is None:
            raise TypeError(
                f"{cls.__name__} must define its own __init__(self, client, ...)"
            )

        # Inspect signature to ensure first parameter after self is `client`
        import inspect

        sig = inspect.signature(init)
        params = list(sig.parameters.values())

        if len(params) < 2 or params[1].name != "client":
            raise TypeError(
                f"{cls.__name__}.__init__ must accept `client` as its second parameter"
            )

    def _get_resolution(self) -> tuple[int, int]:
        ctx = getattr(self.client, "context", None)
        if ctx is not None:
            res = getattr(ctx, "resolution", None)
            if isinstance(res, tuple) and len(res) == 2:
                return cast(tuple[int, int], res)
        return (1, 1)

    @property
    def factor(self) -> int:
        return self.client.context.scale

    def load_sprite(self, filename: str, **kwargs: Any) -> Sprite:
        """Load a sprite and add it to this state."""
        layer = kwargs.pop("layer", 0)
        sprite = load_sprite(filename, **kwargs)
        self.sprites.add(sprite, layer=layer)
        return sprite

    def load_surface(self, surface: Surface, **kwargs: Any) -> Sprite:
        layer = kwargs.pop("layer", 0)
        sprite = load_surface(surface, **kwargs)
        self.sprites.add(sprite, layer=layer)
        return sprite

    def load_animated_sprite(
        self,
        filenames: Iterable[str],
        delay: float,
        scale: float,
        **kwargs: Any,
    ) -> Sprite:
        """Load an animated sprite and add it to this state."""
        layer = kwargs.pop("layer", 0)
        sprite = load_animated_sprite(filenames, delay, scale, **kwargs)
        self.sprites.add(sprite, layer=layer)
        return sprite

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
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

    def scale_int(self, value: int) -> int:
        """Convenience wrapper for client scaling."""
        return self.client.context.scaling.scale_int(value)

    def update(self, dt: float) -> None:
        """
        Time update function for state. Must be overloaded in children.
        """
        self.update_animations(dt)
        self.sprites.update(dt)

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
        self.publish("state_resume")

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
        self.publish("state_pause")

    def shutdown(self) -> None:
        """
        Called when state is removed from stack and will be destroyed.

        This will be called:
        * after update when state is popped

        Make sure to release any references to objects that may cause
        cyclical dependencies.
        """
        self.publish("state_shutdown")

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

    def subscribe(
        self, event_name: str, callback: Callable[..., None], priority: int = 0
    ) -> None:
        self.event_bus.subscribe(event_name, callback, priority)

    def unsubscribe(
        self, event_name: str, callback: Callable[..., None]
    ) -> None:
        if self.event_bus.has_listeners_for_event(event_name):
            self.event_bus.unsubscribe(event_name, callback)

    def publish(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        if self.event_bus.has_listeners_for_event(event_name):
            self.event_bus.publish(event_name, *args, **kwargs)

    def replace_events(self, event_name: str, events: list[Listener]) -> None:
        self.event_bus.clear_event(event_name)

        for listener in events:
            self.event_bus.subscribe(
                event_name,
                listener.callback,
                priority=listener.priority,
            )
