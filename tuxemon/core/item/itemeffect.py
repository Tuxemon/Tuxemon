# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
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
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
# Adam Chevalier <chevalieradam2@gmail.com>
#
# core.item Item handling module.
#
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import pprint
import random
from six.moves import zip_longest
from collections import namedtuple
from tuxemon.core import tools, prepare
from tuxemon.core.technique import Technique
from tuxemon.core.db import db, process_targets
from tuxemon.core.locale import T
from tuxemon.core.control import Control  # for type introspection
assert Control

logger = logging.getLogger(__name__)

class ItemEffect(object):
    """ ItemEffects are executed by items.

    ItemEffect subclasses implement "effects" defined in Tuxemon items.
    All subclasses, at minimum, must implement the following:

    * The ItemEffect.apply() method
    * A meaningful name, which must match the name in item file effects

    By populating the "valid_parameters" class attribute, subclasses
    will be assigned a "parameters" instance attribute that holds the
    parameters passed to the action in the item file.  It is also used
    to check the syntax of effects, by verifying the correct type and
    number of parameters passed.

    Parameters
    ==========

    Tuxemon supports type-checking of the parameters defined in the items.

    valid_parameters may be the following format (may change):

    (type, name)

    * the type may be any valid python type, or even a python class or function
    * type may be a single type, or a tuple of types
    * type, if a tuple, may include None is indicate the parameter is optional
    * name must be a valid python string

    After parsing the parameters of the Item, the parameter's value
    will be passed to the type constructor.

    Example types: str, int, float, Monster, NPC

    (int, "duration")                => duration must be an int
    ((int, float), "duration")       => can be an int or float
    ((int, float, None), "duration") => is optional

    (Monster, "monster_slug")   => a Monster instance will be created
    """
    name = "GenericEffect"
    valid_parameters = list()
    _param_factory = None

    def __init__(self, game, parameters):
        """

        :type game: tuxemon.core.control.Control
        :type parameters: list
        """
        self.game = game
        self.target = target

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
                values = self.cast_values(parameters)
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

    def cast_values(self, parameters):
        """ Change all the string values to the expected type

        This will also check and enforce the correct parameters for actions

        :param parameters:
        :return:
        """

        # TODO: stability/testing
        def cast(i):
            try:
                ve = False
                t, v = i
                try:
                    for tt in t[0]:
                        if tt is None:
                            return None

                        try:
                            return tt(v)
                        except ValueError:
                            ve = True

                except TypeError:
                    if v is None:
                        return None

                    if v == '':
                        return None

                    return t[0](v)

                if ve:
                    raise ValueError

            except ValueError:
                logger.error("Invalid parameters passed:")
                logger.error("expected: {}".format(self.valid_parameters))
                logger.error("got: {}".format(self.raw_parameters))

        try:
            return list(map(cast, zip_longest(self.valid_parameters, parameters)))
        except ValueError:
            logger.error("Invalid parameters passed:")
            logger.error("expected: {}".format(self.valid_parameters))
            logger.error("got: {}".format(self.raw_parameters))
            raise

    def apply(self, target):
        pass