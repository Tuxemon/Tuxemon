# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class MenuAction(EventAction):
    """
    Enable/disable one or more menu.

    Script usage:
        .. code-block::

            menu <act>[,menu]

    Script parameters:
        act: enable or disable
        menu: specific menu (menu_monster, menu_bag, menu_player,
            exit, menu_options, menu_save, menu_load)
            without specification, everything disabled

    eg. menu disable,menu_bag
    eg. menu enable,menu_player

    """

    name = "menu"
    act: str
    menu: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        result = True if self.act == "enable" else False

        if self.menu is None:
            player.menu_bag = result
            player.menu_load = result
            player.menu_monsters = result
            player.menu_save = result
            player.menu_player = result
            player.menu_missions = result
        else:
            if self.menu == "menu_bag":
                player.menu_bag = result
            elif self.menu == "menu_load":
                player.menu_load = result
            elif self.menu == "menu_monsters":
                player.menu_monsters = result
            elif self.menu == "menu_save":
                player.menu_save = result
            elif self.menu == "menu_player":
                player.menu_player = result
            elif self.menu == "menu_missions":
                player.menu_missions = result
            else:
                raise ValueError(f"{self.menu} isn't valid.")
