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

from typing import NamedTuple, Optional, final

from tuxemon.event.eventaction import EventAction


class TuxepediaPrintActionParameters(NamedTuple):
    monster_slug: Optional[str]


@final
class TuxepediaPrintAction(EventAction[TuxepediaPrintActionParameters]):
    """
    Print the current value of Tuxepedia to the console.

    If no monster is specified, print out values of all Tuxepedia.

    Script usage:
        .. code-block::

            tuxepedia_print
            tuxepedia_print <monster_slug>

        Script parameters:
            monster_slug: Monster slug name (e.g. "rockitten").

    """

    name = "tuxepedia_print"
    param_class = TuxepediaPrintActionParameters

    def start(self) -> None:
        var = self.session.player.tuxepedia

        monster_slug = self.parameters.monster_slug
        if monster_slug:
            if monster_slug in var:
                print(f"{monster_slug}: {var[monster_slug]}")
            else:
                print(f"'{monster_slug}' has not been seen yet.")
        else:
            print(var)
