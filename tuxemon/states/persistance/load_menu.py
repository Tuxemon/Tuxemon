# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Optional

from pygame.rect import Rect

from tuxemon.menu.interface import MenuItem

from .save_menu import SLOT_HEIGHT_RATIO, SLOT_WIDTH_RATIO, SaveMenuState

logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    def __init__(self, load_slot: Optional[int] = None) -> None:
        super().__init__()
        if load_slot:
            self.selected_index = load_slot - 1
            self.on_menu_selection(None)

    def initialize_items(self) -> None:
        rect = self.client.screen.get_rect()
        slot_rect = Rect(
            0,
            0,
            rect.width * SLOT_WIDTH_RATIO,
            rect.height // SLOT_HEIGHT_RATIO,
        )
        for i in range(self.number_of_slots):
            item = self.create_menu_item(slot_rect, i + 1, selectable=False)
            self.add(item)

    def on_menu_selection(self, menuitem: Optional[MenuItem[None]]) -> None:
        self.client.event_engine.execute_action(
            "load_game",
            [self.selected_index],
            True,
        )
