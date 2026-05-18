# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.session import Session


@final
@dataclass
class MenuAction(EventAction):
    """
    Toggle visibility of one or more world menu entries, or apply a preset.

    Script usage:
        .. code-block::

            menu <flag>[,menu_1:menu_2:...]   # toggles specific menus
            menu <preset>                     # applies preset config

    Parameters:
        flag: "enable" or "disable", applied to specified menus (or all)
        preset: one of defined presets ("minimal", etc.)

    Examples:
        menu reset                         > clears all menu flags
        menu enable                        > enables all menus
        menu disable,menu_bag:menu_player  > disables specified menus
        menu enable,all                    > enables all menus
        menu minimal                       > applies "minimal" preset
    """

    name = "menu"
    act: str
    menu: str | None = None

    def start(self, session: Session) -> None:
        flags = session.world.menu_manager.menu_flags
        valid_keys = flags.DEFAULT_PRESETS["full"].keys()
        presets = flags.DEFAULT_PRESETS.keys()

        if self.act == "reset":
            flags.reset_flags()
            flags.apply_preset("raw")
            session.world.menu_manager.update_menu_display()
            self.stop()
            return

        if self.act in presets:
            flags.apply_preset(self.act)
        else:
            if self.act not in ("enable", "disable"):
                raise ValueError(
                    f"Invalid menu action: '{self.act}' must be 'enable', 'disable', or a preset name."
                )

            result = self.act == "enable"

            if self.menu is None or self.menu.strip() == "all":
                for key in valid_keys:
                    flags.set_enabled(key, result)
            else:
                keys = [k.strip() for k in self.menu.split(":")]
                for key in keys:
                    flags.set_enabled(key, result)

        session.world.menu_manager.update_menu_display()
