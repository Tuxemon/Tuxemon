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
#
# Adam Chevalier <chevalierAdam2@gmail.com>
#

from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction


class AssignNameActionParameters(NamedTuple):
    slug: str


@final
class AssignNameAction(EventAction[AssignNameActionParameters]):
    """
    Assign name to the player without opening the input.

    Script usage:
        .. code-block::

            assign_name <slug>

    """

    name = "assign_name"
    param_class = AssignNameActionParameters

    def start(self) -> None:
        self.session.player.name = self.parameters.slug
