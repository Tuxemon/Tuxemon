# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class TuxepediaPrintAction(EventAction):
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
    monster_slug: Optional[str] = None

    def start(self) -> None:
        var = self.session.player.tuxepedia

        monster_slug = self.monster_slug
        if monster_slug:
            if monster_slug in var:
                print(f"{monster_slug}: {var[monster_slug]}")
            else:
                print(f"'{monster_slug}' has not been seen yet.")
        else:
            print(var)
