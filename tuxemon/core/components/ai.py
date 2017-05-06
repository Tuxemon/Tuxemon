#!/usr/bin/python
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
# core.components.ai Artificial intelligence module.
#
#
import logging
from random import choice

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)


# Class definition for an AI model.
# TODO: use ABC meta.  impl. depends on six/future decision
# TODO: allow AI to target self or own team
class AI(object):
    """ Base class for an AI model object.
    """

    def make_decision(self, npc, opponents):
        """ Given a npc, and list of opponents, decide an action to take

        :param npc: The monster whose decision is being decided
        :param opponents: List of possible targets
        :return: Technique, Target
        """
        raise NotImplementedError


class SimpleAI(AI):
    """ Very simple AI.  Always uses first technique against first opponent.
    """

    def make_decision(self, npc, opponents):
        """ Given a npc, and list of opponents, decide an action to take

        :param npc: The monster whose decision is being decided
        :param opponents: List of possible targets
        :return: Technique, Target
        """
        return npc.moves[0], opponents[0]


class RandomAI(AI):
    """ AI will use random technique against random opponent
    """

    def make_decision(self, npc, opponents):
        """ Given a npc, and list of opponents, decide an action to take

        :param npc: The monster whose decision is being decided
        :param opponents: List of possible targets
        :return: Technique, Target
        """
        # TODO: healing and whatnot
        return choice(npc.moves), choice(opponents)
