# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect

from tuxemon.menu.interface import MenuItem
from tuxemon.tools import open_dialog

from .save_menu import SLOT_HEIGHT_RATIO, SLOT_WIDTH_RATIO, SaveMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

logger = logging.getLogger(__name__)


class LoadMenuState(SaveMenuState):
    name: ClassVar[str] = "LoadMenuState"

    def __init__(
        self, client: BaseClient, load_slot: int | None = None, **kwargs: Any
    ) -> None:
        super().__init__(client=client, **kwargs)
        if load_slot:
            self.selected_index = load_slot - 1
            self.on_menu_selection(None)

    def initialize_items(self) -> None:
        rect = self.client.context.rect.copy()
        slot_rect = Rect(
            0,
            0,
            rect.width * SLOT_WIDTH_RATIO,
            rect.height // SLOT_HEIGHT_RATIO,
        )
        for i in range(self.number_of_slots):
            item = self.create_menu_item(slot_rect, i + 1, selectable=False)
            self.add(item)

    def on_menu_selection(self, menuitem: MenuItem[None] | None) -> None:
        logger.warning("Load attempt blocked in online-world mode.")
        self.client.remove_state_by_name("LoadMenuState")
        open_dialog(
            self.client,
            ["Loading local files is disabled in online-world mode."],
        )
