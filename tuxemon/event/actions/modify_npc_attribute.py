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
from tuxemon.event import get_npc
from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final


class ModifyNpcAttributeActionParameters(NamedTuple):
    npc_slug: str
    name: str
    value: float


@final
class ModifyNpcAttributeAction(
    EventAction[ModifyNpcAttributeActionParameters],
):
    """Modifies the given attribute of the npc by modifier. By default
    this is achieved via addition, but prepending a '%' will cause it to be
    multiplied by the attribute.

    Valid Parameters: slug, attribute, modifier

    EventAction parameter 'modifier' must be a number (positive or negative)
    """

    name = "modify_npc_attribute"
    param_class = ModifyNpcAttributeActionParameters

    def start(self) -> None:
        npc = get_npc(self.session, self.parameters[0])
        attribute = self.parameters[1]
        modifier = self.parameters[2]
        CommonAction.modify_character_attribute(npc, attribute, modifier)
