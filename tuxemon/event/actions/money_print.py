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

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class MoneyPrintAction(EventAction):
    """
    Print the current value of money dictionary to the console.

    If no entity is specified, print out values of all money dictionary.

    Script usage:
        .. code-block::

            money_print
            money_print <slug>

        Script parameters:
            slug: Slug name (e.g. player or NPC, etc.).

    """

    name = "money_print"
    slug: Optional[str] = None

    def start(self) -> None:
        var = self.session.player.money

        slug = self.slug
        if slug:
            if slug in var:
                print(f"{slug}: {var[slug]}")
            else:
                print(f"'{slug}' is broke.")
        else:
            print(var)
