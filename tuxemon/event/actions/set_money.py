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

from tuxemon.event.eventaction import EventAction


class SetMoneyActionParameters(NamedTuple):
    wallet: str
    amount: int


@final
class SetMoneyAction(EventAction[SetMoneyActionParameters]):
    """
    Set the key and value in the money dictionary.

    Script usage:
        .. code-block::

            set_money <slug>,<amount>

    Script parameters:
        slug: Slug name (e.g. player or NPC, etc.).
        amount: amoung of money

    """

    name = "set_money"
    param_class = SetMoneyActionParameters

    def start(self) -> None:
        player = self.session.player.money

        # Read the parameters
        wallet = self.parameters[0]
        amount = self.parameters[1]

        # Append the money with a key
        player[str(wallet)] = amount
