#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Leif Theden <leif.theden@gmail.com>
#

from __future__ import annotations
import logging
from collections import namedtuple

from tuxemon.tools import cast_parameters_to_namedtuple, NamedTupleProtocol
from typing import Optional, Type, Sequence, Any, Tuple, NamedTuple, Union,\
    TypeVar, Generic
from types import TracebackType
from tuxemon.session import Session
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


ParameterClass = TypeVar("ParameterClass", bound=NamedTupleProtocol)


class EventAction(ABC, Generic[ParameterClass]):
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
    * type, if a tuple, may include None is indicate the parameter is optional
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

    name = "GenericAction"

    def __init__(
        self,
        session: Session,
        parameters: Sequence[Any],
    ) -> None:

        self.session = session

        # if you need the parameters before they are processed, use this
        self.raw_parameters = parameters

        # parse parameters
        try:
            if self.param_class._fields:

                # cast the parameters to the correct type, as defined in cls.valid_parameters
                self.parameters = cast_parameters_to_namedtuple(
                    parameters,
                    self.param_class,
                )
            else:
                self.parameters = parameters

        except:
            logger.error(f"error while parsing for {self.name}")
            logger.error(f"cannot parse parameters: {parameters}")
            logger.error(self.param_class)
            logger.error("please check the parameters and verify they are correct")
            self.parameters = None

        self._done = False

    @property
    @abstractmethod
    def param_class(self) -> Type[ParameterClass]:
        raise NotImplementedError

    def __enter__(self) -> None:
        """
        Called only once, when the action is started.

        Context Protocol.

        """
        self.start()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Called only once, when action is stopped and needs to close.

        Context Protocol.

        """
        self.cleanup()

    def stop(self) -> None:
        """
        Call when the action is done.

        EventAction will be removed at end of frame.

        If an EventAction overrides update, it must eventually call this
        method.

        """
        self._done = True

    def execute(self) -> None:
        """
        Blocking call to run the action. Will setup and cleanup action.

        This may cause the game to hang if an action is waiting on game
        changes.

        """
        with self:
            self.run()

    def run(self) -> None:
        """
        Blocking call to run the action, without start or cleanup.

        It is better to use EventAction.execute().

        This may cause the game to hang if an action is waiting on game
        changes.

        """
        while not self.done:
            self.update()

    @property
    def done(self) -> bool:
        """
        Will be true when action is finished.

        If you need the action to stop, call EventAction.stop().

        """
        return self._done

    @abstractmethod
    def start(self) -> None:
        """
        Called only once, when the action is started.

        For all actions, you will need to override this method.

        For actions that only need to run one frame you can simply
        put all the code here.  If the action will need to run over
        several frames, you can init your action here, then override
        the update method.

        """
        raise NotImplementedError

    def update(self) -> None:
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
        self.stop()

    def cleanup(self) -> None:
        """
        Called only once, when action is stopped and needs to close.

        You do not need to override this, but it may be useful for some
        actions which require special handling before they are closed.

        """
        pass
