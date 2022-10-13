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

from typing import NamedTuple, Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.item.economy import Economy


class SetEconomyActionParameters(NamedTuple):
    npc_slug: str
    economy_slug: Union[str, None]


@final
class SetEconomyAction(EventAction[SetEconomyActionParameters]):
    """
    Set the economy (prices of items) of the npc or player.

    Script usage:
        .. code-block::

            set_economy <npc_slug>,<economy_slug>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        economy_slug: Slug of an economy.

    """

    name = "set_economy"
    param_class = SetEconomyActionParameters

    def start(self) -> None:
        npc = get_npc(self.session, self.parameters.npc_slug)
        assert npc
        if self.parameters.economy_slug is None:
            npc.economy = Economy("default")

            return

        npc.economy = Economy(self.parameters.economy_slug)
