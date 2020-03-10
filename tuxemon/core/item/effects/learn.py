# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
# Adam Chevalier <chevalieradam2@gmail.com>
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tuxemon.core.item.itemeffect import ItemEffect
from tuxemon.core.technique import Technique


class LearnEffect(ItemEffect):
    """This effect teaches the target the technique in the parameters.
    """
    name = "learn"
    valid_parameters = [
        (str, "technique")
    ]

    def apply(self, target):
        tech = Technique()
        tech.load(self.parameters.technique)
        target.learn(tech)

        return {"success": True}
