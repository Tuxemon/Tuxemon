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
# Derek Clark <derekjohn.clark@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#
#
"""

Do not import platform-specific libraries such as pygame.
Graphics/audio operations should go to their own modules.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from six.moves import zip_longest

from tuxemon.compat.rect import Rect
from tuxemon.core import prepare

logger = logging.getLogger(__name__)


def get_cell_coordinates(rect, point, size):
    """Find the cell of size, within rect, that point occupies."""
    cell = [None, None]
    point = (point[0] - rect.x, point[1] - rect.y)
    cell[0] = (point[0] // size[0]) * size[0]
    cell[1] = (point[1] // size[1]) * size[1]
    return tuple(cell)


def transform_resource_filename(*filename):
    """ Appends the resource folder name to a filename

    :param filename: String
    :rtype: basestring
    """
    return prepare.fetch(*filename)


def new_scaled_rect(*args, **kwargs):
    """ Create a new rect and scale it

    :param args: Normal args for a Rect
    :param kwargs: Normal kwargs for a Rect
    :rtype: tuxemon.compat.rect.Rect
    """
    rect = Rect(*args, **kwargs)
    return scale_rect(rect)


def scale_rect(rect, factor=prepare.SCALE):
    """ Scale a rect.  Returns a new object.

    :param rect: pygame Rect
    :param factor: int
    :rtype: tuxemon.compat.rect.Rect
    """
    return Rect([i * factor for i in list(rect)])


def scale_sequence(sequence):
    """ Scale the thing

    :param sequence:
    :rtype: list
    """
    return [i * prepare.SCALE for i in sequence]


def scale(number):
    """ Scale the thing

    :param number: int
    :rtype: int
    """
    return prepare.SCALE * number


def check_parameters(parameters, required=0, exit=True):
    """
    Checks to see if a given list has the required number of items
    """
    if len(parameters) < required:
        import inspect
        calling_function = inspect.stack()[1][3]
        logger.error("'" + calling_function + "' requires at least " + str(required) + "parameters.")
        if exit:
            import sys
            sys.exit(1)
        return False

    else:
        return True


def calc_dialog_rect(screen_rect):
    """ Return a rect that is the area for a dialog box on the screen

    :param screen_rect:
    :return:
    """
    rect = screen_rect.copy()
    if prepare.CONFIG.large_gui:
        rect.height *= .4
        rect.bottomleft = screen_rect.bottomleft
    else:
        rect.height *= .25
        rect.width *= .8
        rect.center = screen_rect.centerx, screen_rect.bottom - rect.height
    return rect


def open_dialog(game, text, avatar=None, menu=None):
    """ Open a dialog with the standard window size

    :param game:
    :param text: list of strings
    :param avatar: optional avatar sprite
    :param menu: optional menu object

    :rtype: core.states.dialog.DialogState
    """
    rect = calc_dialog_rect(game.screen.get_rect())
    return game.push_state("DialogState", text=text, avatar=avatar, rect=rect, menu=menu)


def nearest(l):
    """ Use rounding to find nearest tile

    :param l:
    :return:
    """
    return tuple(int(round(i)) for i in l)


def trunc(l):
    return tuple(int(i) for i in l)


def number_or_variable(game, value):
    """ Returns a numeric game variable by its name
    If value is already a number, convert from string to float and return that

    :param game:
    :param value: Union[str, float, int]

    :rtype: float

    :raises: ValueError
    """
    player = game.player1
    if value.isdigit():
        return float(value)
    else:
        try:
            return float(player.game_variables[value])
        except (KeyError, ValueError, TypeError):
            logger.error("invalid number or game variable {}".format(value))
            raise ValueError


def cast_values(parameters, valid_parameters):
    """ Change all the string values to the expected type

    This will also check and enforce the correct parameters for actions

    :param parameters:
    :param valid_parameters:
    :return:
    """

    # TODO: stability/testing
    def cast(i):
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

    try:
        return list(map(cast, zip_longest(valid_parameters, parameters)))
    except ValueError:
        logger.error("Invalid parameters passed:")
        logger.error("expected: {}".format(valid_parameters))
        logger.error("got: {}".format(parameters))
        raise
