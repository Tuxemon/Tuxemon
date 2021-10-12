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


class SetNpcAttributeActionParameters(NamedTuple):
    npc_slug: str
    name: str
    value: str


@final
class SetNpcAttributeAction(EventAction[SetNpcAttributeActionParameters]):
    """
    Set the given attribute of the npc to the given value.

    Script usage:
        .. code-block::

            set_npc_attribute <npc_slug>,<name>,<value>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        name: Name of the attribute.
        value: Value of the attribute.

    """

    name = "set_npc_attribute"
    param_class = SetNpcAttributeActionParameters

    def start(self) -> None:
        npc = get_npc(self.session, self.parameters[0])
        assert npc
        attribute = self.parameters[1]
        value = self.parameters[2]
        CommonAction.set_character_attribute(npc, attribute, value)
