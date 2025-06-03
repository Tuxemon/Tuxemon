# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, ClassVar, Optional

from tuxemon.constants.paths import ACTIONS_PATH
from tuxemon.plugin import load_plugins
from tuxemon.session import Session
from tuxemon.tools import cast_dataclass_parameters

logger = logging.getLogger(__name__)


class ActionContextManager:
    def __init__(self, action: EventAction, session: Session) -> None:
        self.action = action
        self.session = session

    def __enter__(self) -> EventAction:
        """
        Called once when entering the context.

        Ensures the action is started, unless it is marked as cancelled.
        Logs a warning if the action is cancelled.

        Returns:
            EventAction: The managed action.
        """
        if self.action.cancelled:
            logger.warning("Event is cancelled, not starting")
        else:
            self.action.start(self.session)
        return self.action

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Called once when exiting the context.

        Ensures the action is properly cleaned up, unless it is marked as cancelled.
        Logs a warning if the action is cancelled.
        """
        if self.action.cancelled:
            logger.warning("Event is cancelled, not cleaning up")
            return
        self.action.cleanup(self.session)


@dataclass
class EventAction(ABC):
    """EventActions are executed during gameplay.

    EventAction subclasses implement "actions" defined in Tuxemon maps.
    All subclasses, at minimum, must implement the following:

    * The EventAction.start() method
    * A meaningful name, which must match the name in map file actions

    By populating the "valid_parameters" class attribute, subclasses
    will be assigned a "parameters" instance attribute that holds the
    parameters passed to the action in the map file.  It is also used
    to check the syntax of actions, by verifying the correct type and
    number of parameters passed.

    If an EventAction does not implement the update method, it will only
    run for one frame.  If it does implement the update method, then it
    will continue to run until it is stopped, or the EventEngine is stopped.

    If you wish to stop an EventAction, call the stop method.  Calling
    stop() signals to the EventEngine that this EventAction is done,
    and can be removed from the processing loop at the end of the frame.

    Update will be called every frame the EventAction is running,
    including the first frame it is started.  You should eventually
    stop the action during update.

    The EventAction class supports the context protocol, and you may
    also use them outside of the EventEngine, but can only be run
    in a blocking manner.  Do not execute EventActions outside the Engine
    if the action will block forever, as it will freeze the game.


    **Parameters**

    ** this is a work-in-progress feature, that may change in time **

    Tuxemon supports type-checking of the parameters defined in the maps.

    valid_parameters may be the following format (may change):

    (type, name)

    * the type may be any valid python type, or even a python class or function
    * type may be a single type, or a tuple of types
    * type, if a tuple, may include None to indicate the parameter is optional
    * name must be a valid python string

    After parsing the parameters of the MapAction, the parameter's value
    will be passed to the type constructor.

    Example types: str, int, float, Monster, Item

    (int, "duration")                => duration must be an int
    ((int, float), "duration")       => can be an int or float
    ((int, float, None), "duration") => is optional

    (Monster, "monster_slug")   => a Monster instance will be created

    Parameters:
        session: Object containing the session information.
        parameters: Parameters of the action.
    """

    name: ClassVar[str]
    _done: bool = field(default=False, init=False)
    _skip: bool = field(default=False, init=False)
    cancelled: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        cast_dataclass_parameters(self)

    def stop(self) -> None:
        """
        Call when the action is done.

        EventAction will be removed at end of frame.

        If an EventAction overrides update, it must eventually call this
        method.
        """
        self._done = True

    def execute(self, session: Session) -> None:
        """
        Blocking call to run the action. Will setup and cleanup action.

        This may cause the game to hang if an action is waiting on game
        changes.
        """
        if self.cancelled:
            logger.debug("Action is cancelled, not executing")
            return
        try:
            with ActionContextManager(self, session):
                self.run(session)
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            raise

    def run(self, session: Session) -> None:
        """
        Blocking call to run the action, without start or cleanup.

        It is better to use EventAction.execute().

        This may cause the game to hang if an action is waiting on game
        changes.
        """
        if self.cancelled:
            logger.debug("Action is cancelled, not running")
            return
        try:
            while not self.done and not self.cancelled:
                if self._skip:
                    return
                else:
                    self.update(session)
        except Exception as e:
            logger.error(f"Error running action: {e}")
            raise

    @property
    def done(self) -> bool:
        """
        Will be true when action is finished.

        If you need the action to stop, call EventAction.stop().
        """
        return self._done

    @abstractmethod
    def start(self, session: Session) -> None:
        """
        Called only once, when the action is started.

        For all actions, you will need to override this method.

        For actions that only need to run one frame you can simply
        put all the code here.  If the action will need to run over
        several frames, you can init your action here, then override
        the update method.
        """
        if self.cancelled:
            logger.debug("Action is cancelled, not starting")
            self.stop()
            return
        try:
            # start the action
            pass
        except Exception as e:
            logger.error(f"Error starting action: {e}")
            raise

    def update(self, session: Session) -> None:
        """
        Called once per frame while action is running.

        It is also called on the first frame when EventAction is started.

        If you do not override this, then the action will stop after it is
        started, and live for only one frame.

        If you do override this, then this method will be run every frame
        until EventAction.stop() is called.  If you do not ever call stop(),
        then this action will block all others in the list and will continue
        to run until the parent EventEngine is stopped.
        """
        if self.cancelled:
            logger.debug("Action is cancelled, not updating")
            return
        try:
            self.stop()
        except Exception as e:
            logger.error(f"Error updating action: {e}")
            raise

    def cancel(self) -> None:
        """
        Cancels the action.

        This method sets the `cancelled` attribute to `True`, which will prevent
        the action from being executed.
        """
        self.cancelled = True

    def cleanup(self, session: Session) -> None:
        """
        Called only once, when action is stopped and needs to close.

        You do not need to override this, but it may be useful for some
        actions which require special handling before they are closed.
        """
        if self.cancelled:
            logger.debug("Action is cancelled, not cleaning up")
            return
        try:
            # clean up the action
            pass
        except Exception as e:
            logger.error(f"Error cleaning up action: {e}")
            raise


class ActionManager:
    def __init__(self) -> None:
        self.actions = load_plugins(
            ACTIONS_PATH.as_posix(),
            "actions",
            interface=EventAction,  # type: ignore[type-abstract]
        )

    def get_action(
        self,
        name: str,
        parameters: Optional[Sequence[Any]] = None,
    ) -> Optional[EventAction]:
        """
        Get an action that is loaded into the engine.

        A new instance will be returned each time.

        Return ``None`` if action is not loaded.

        Parameters:
            name: Name of the action.
            parameters: List of parameters that the action accepts.

        Returns:
            New instance of the action with the appropriate parameters if
            that action is loaded. ``None`` otherwise.
        """
        parameters = parameters or []

        try:
            action = self.actions[name]

        except KeyError:
            error = f'Error: EventAction "{name}" not implemented'
            logger.warning(error)
            return None

        if parameters == [""]:
            return action()

        try:
            return action(*parameters)
        except TypeError as e:
            logger.warning(
                f"Error instantiating {action} with parameters {parameters}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error instantiating {action} with parameters {parameters}: {e}"
            )
            return None

    def get_actions(self) -> list[type[EventAction]]:
        """Return list of EventActions."""
        return list(self.actions.values())
