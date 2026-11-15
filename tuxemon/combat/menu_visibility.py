# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations


class MenuProfiles:
    @staticmethod
    def default_trainer_battle() -> tuple[dict[str, str], dict[str, bool]]:
        return (
            {
                "menu_fight": "open_technique_menu",
                "menu_monster": "open_swap_menu",
                "menu_item": "open_item_menu",
                "menu_forfeit": "forfeit",
            },
            {
                "menu_fight": True,
                "menu_monster": True,
                "menu_item": True,
                "menu_forfeit": False,  # default visibility
            },
        )

    @staticmethod
    def default_monster_battle() -> tuple[dict[str, str], dict[str, bool]]:
        return (
            {
                "menu_fight": "open_technique_menu",
                "menu_monster": "open_swap_menu",
                "menu_item": "open_item_menu",
                "menu_run": "run",
            },
            {
                "menu_fight": True,
                "menu_monster": True,
                "menu_item": True,
                "menu_run": True,
            },
        )
