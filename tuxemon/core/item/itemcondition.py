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
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Adam Chevalier <chevalieradam2@gmail.com>
#



import logging
from collections import namedtuple

from tuxemon.core.tools import cast_values

logger = logging.getLogger(__name__)


class ItemCondition:
    """ ItemConditions are evaluated by items.

    ItemCondition subclasses implement "conditions" defined in Tuxemon items.
    All subclasses, at minimum, must implement the following:

    * The ItemCondition.test() method
    * A meaningful name, which must match the name in item file effects

    By populating the "valid_parameters" class attribute, subclasses
    will be assigned a "parameters" instance attribute that holds the
    parameters passed to the condition in the item file.  It is also used
    to check the syntax of conditions, by verifying the correct type and
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

    (int, "level")                => level must be an int
    ((int, float), "level")       => can be an int or float
    ((int, float, None), "level") => is optional

    (Monster, "monster_slug")   => a Monster instance will be created
    """
    name = "GenericCondition"
    valid_parameters = list()
    _param_factory = None

    def __init__(self, context, session,  user, parameters):
        """

        :type context: str
        :type user: tuxemon.core.NPC
        :type parameters: list
        """

        self.session = session
        self.user = user
        self.context = context

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

    def test(self, target):
        """ Return True if satisfied, or False if not

        :param target: the target of the item's use.
        :rtype: bool
        """
        return True
