# -*- coding: utf-8 -*-
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from collections import namedtuple

from tuxemon.core.tools import cast_values

logger = logging.getLogger(__name__)


class EventAction(object):
    """ EventActions are executed during gameplay.

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


    Parameters
    ==========

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
    """
    name = "GenericAction"
    valid_parameters = list()
    _param_factory = None

    def __init__(self, session, parameters):
        """

        :type session: tuxemon.session.Session
        :type parameters: list
        """
        self.session = session

        # TODO: METACLASS
        # make a namedtuple class that will generate the parameters
        # the patching of the class attribute should only happen once
        if self.__class__._param_factory is None:
            self.__class__._param_factory = namedtuple("parameters", [i[1] for i in self.valid_parameters])

        # if you need the parameters before they are processed, use this
        self.raw_parameters = parameters

        # parse parameters
        try:
            if self.valid_parameters:

                # cast the parameters to the correct type, as defined in cls.valid_parameters
                values = cast_values(parameters, self.valid_parameters)
                self.parameters = self._param_factory(*values)
            else:
                self.parameters = parameters

        except:
            logger.error("error while parsing for {}".format(self.name))
            logger.error("cannot parse parameters: {}".format(parameters))
            logger.error(self.valid_parameters)
            logger.error("please check the parameters and verify they are correct")
            self.parameters = None

        self._done = False

    def __enter__(self):
        """ Called only once, when the action is started

        Context Protocol

        :return:
        """
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Called only once, when action is stopped and needs to close

        Context Protocol

        :return:
        """
        self.cleanup()

    def stop(self):
        """ Call when the action is done.  EventAction will be removed at end of frame.

        If an EventAction overrides update, it must eventually call this method.

        :return:
        """
        self._done = True

    def execute(self):
        """ Blocking call to run the action.  Will setup and cleanup action.

        This may cause the game to hang if an action is waiting on game changes

        :return:
        """
        with self:
            self.run()

    def run(self):
        """ Blocking call to run the action, without start or cleanup

        It is better to use EventAction.execute()

        This may cause the game to hang if an action is waiting on game changes

        :return:
        """
        while not self.done:
            self.update()

    @property
    def done(self):
        """ Will be true when action is finished.  If you need the
            action to stop, call EventAction.stop()

        :return:
        """
        return self._done

    def start(self):
        """ Called only once, when the action is started

        For all actions, you will need to override this method.

        For actions that only need to run one frame you can simply
        put all the code here.  If the action will need to run over
        several frames, you can init your action here, then override
        the update method.

        :return:
        """
        raise NotImplementedError

    def update(self):
        """ Called once per frame while action is running, including the
            first frame when EventAction is started.

        If you do not override this, then the action will stop after it is
        started, and live for only one frame.

        If you do override this, then this method will be run every frame
        until EventAction.stop() is called.  If you do not ever call stop(),
        then this action will block all others in the list and will continue
        to run until the parent EventEngine is stopped.

        :return:
        """
        self.stop()

    def cleanup(self):
        """ Called only once, when action is stopped and needs to close

        You do not need to override this, but it may be useful for some
        actions which require special handling before they are closed.

        :return:
        """
        pass
