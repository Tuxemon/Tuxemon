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

from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction


class ModifyPlayerAttributeActionParameters(NamedTuple):
    name: str
    value: str


@final
class ModifyPlayerAttributeAction(
    EventAction[ModifyPlayerAttributeActionParameters],
):
    """
    Modify the given attribute of the player character by modifier.

    By default this is achieved via addition, but prepending a '%' will cause
    it to be multiplied by the attribute.

    Script usage:
        .. code-block::

            modify_player_attribute <name>,<value>

    Script parameters:
        name: Name of the attribute to modify.
        value: Value of the attribute modifier.

    """

    name = "modify_player_attribute"
    param_class = ModifyPlayerAttributeActionParameters

    def start(self) -> None:
        attribute = self.parameters[0]
        modifier = self.parameters[1]
        CommonAction.modify_character_attribute(
            self.session.player,
            attribute,
            modifier,
        )
