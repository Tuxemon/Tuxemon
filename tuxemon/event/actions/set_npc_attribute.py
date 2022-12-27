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

from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class SetNpcAttributeAction(EventAction):
    """
    Set the given attribute of the npc to the given value.

    Script usage:
        .. code-block::

            set_npc_attribute <npc_slug>,<attribute>,<value>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        attribute: Name of the attribute.
        value: Value of the attribute.

    """

    name = "set_npc_attribute"
    npc_slug: str
    attribute: str
    value: str

    def start(self) -> None:
        npc = get_npc(self.session, self.npc_slug)
        assert npc
        CommonAction.set_character_attribute(npc, self.attribute, self.value)
