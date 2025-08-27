# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class MenuVisibility:
    menu_fight: bool = True
    menu_monster: bool = True
    menu_item: bool = True
    menu_forfeit: bool = False
    menu_run: bool = True

    def update_visibility(self, key: str, visible: bool) -> None:
        if hasattr(self, key):
            setattr(self, key, visible)
        else:
            raise ValueError(f"Invalid menu item key: {key}")

    def reset_to_default(self) -> None:
        self.__dict__.update(MenuVisibility().__dict__)
