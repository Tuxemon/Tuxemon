# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.menu import Menu

from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.transitions import SlideRight
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import DIMGRAY_COLOR
from tuxemon.platform.events import PlayerInput
from tuxemon.states.monster_menu import MonsterMenuHandler

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.world.manager import MenuItem, WorldMenuManager

logger = logging.getLogger(__name__)


WorldMenuGameObj = Callable[[], object]


def add_menu_items_to_pygame_menu(
    menu: Menu, items: list[MenuItem], resolution: tuple[int, int]
) -> None:
    """Helper function to add items to a pygame_menu.Menu instance."""
    menu.clear()
    menu.add.vertical_fill()

    for item in items:
        label = item.label
        callback = item.callback
        if item.enabled:
            menu.add.button(label, callback)
        else:
            menu.add.label(
                label,
                font_color=DIMGRAY_COLOR,
            )
        menu.add.vertical_fill()

    width, height = resolution
    widgets_size = menu.get_size(widget=True)
    b_width, b_height = menu.get_scrollarea().get_border_size()
    menu.resize(
        widgets_size[0],
        height - 2 * b_height,
        position=(width + b_width, b_height, False),
    )


class WorldMenuState(PygameMenuState):
    """Menu for the world state."""

    name: ClassVar[str] = "WorldMenuState"

    def __init__(
        self,
        client: BaseClient,
        menu_manager: WorldMenuManager,
        character: NPC,
        **kwargs: Any,
    ) -> None:
        """Initialize menu state and build menu separately."""
        self.char = character
        width, height = client.context.resolution

        super().__init__(
            client=client, height=height, transition=SlideRight(), **kwargs
        )

        self.menu_manager = menu_manager
        self.menu_manager.set_menu_renderer(self)
        self.update_menu_from_manager()
        self.handler = MonsterMenuHandler(self.client, self.char.party)

    def update_menu_from_manager(self) -> None:
        """Refreshes the menu display using items provided by the manager."""
        display = self.menu_manager.build_current_menu_items(self.char)
        resolution = self.client.context.resolution
        add_menu_items_to_pygame_menu(self.menu, display, resolution)

    def open_monster_menu(self) -> None:
        self.handler.open_monster_menu()

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        if (
            event.button in (buttons.START, buttons.B, buttons.BACK)
            and event.pressed
        ):
            self.client.pop_state()
            return None
        return super().process_event(event)
