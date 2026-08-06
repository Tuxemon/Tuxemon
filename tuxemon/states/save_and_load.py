# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.platform.const import buttons
from tuxemon.save_system.save_manager import SaveManager
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.menu_options import MenuOptions, create_choice_options
from tuxemon.ui.text import draw_text

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput
    from tuxemon.save_system.save_state import SaveData

logger = logging.getLogger(__name__)

SLOT_WIDTH_RATIO = 0.80
SLOT_HEIGHT_RATIO = 6
PAGE_LABEL_WIDTH = 80
PAGE_LABEL_HEIGHT = 30
PAGE_LABEL_MARGIN_RIGHT = 120
PAGE_LABEL_MARGIN_BOTTOM = 60


class PaginatedMenuState(PopUpMenu[None]):
    """
    Shared pagination logic for SaveMenuState and LoadMenuState.
    Handles:
      - LEFT/RIGHT page switching
      - snapping selection after switching
      - drawing page indicator
    """

    name: ClassVar[str] = "PaginatedMenuState"

    def __init__(self, client: BaseClient, **kwargs: Any):
        super().__init__(client=client, **kwargs)

    def reload_items(self) -> None:
        super().reload_items()
        self._align_page_to_selection()

    def _align_page_to_selection(self) -> None:
        """
        Open on the page that contains the requested selection.
        The menu can be opened with a ``selected_index`` taken from the
        current save slot, which may live on a later page. Without aligning
        the page, the selection would point off the visible page, leaving the
        cursor on nothing and crashing on the first cursor move. Setting the
        page and snapping guarantees a valid, visible selection.
        """
        page_size = self.menu_items.page_size
        if not page_size:
            return

        self.menu_items.set_page(self.selected_index // page_size)
        self.selected_index = self.menu_items.snap_selection(
            self.selected_index
        )

    def _snap_selection_to_page(self) -> None:
        """Delegate snapping to VisualSpriteList."""
        self.selected_index = self.menu_items.snap_selection(
            self.selected_index
        )
        previous = None
        selected = self.get_selected_item()
        self.cursor_controller.update_selection_focus(
            previous, selected, animate=False
        )

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        """Unified LEFT/RIGHT pagination."""
        if event.button == buttons.LEFT and self.menu_items.has_prev_page:
            self.menu_items.prev_page()
            self._snap_selection_to_page()
            return None

        if event.button == buttons.RIGHT and self.menu_items.has_next_page:
            self.menu_items.next_page()
            self._snap_selection_to_page()
            return None

        return super().process_event(event)

    def draw(self, surface: Surface) -> None:
        """Draw popup + page indicator."""
        super().draw(surface)

        label = self.menu_items.page_label()
        if not label:
            return

        popup_rect = self.rect

        text_rect = Rect(
            popup_rect.right - PAGE_LABEL_MARGIN_RIGHT,
            popup_rect.bottom - PAGE_LABEL_MARGIN_BOTTOM,
            PAGE_LABEL_WIDTH,
            PAGE_LABEL_HEIGHT,
        )

        draw_text(
            surface,
            label,
            text_rect,
            scaling=self.client.context.scaling,
            font=self.font,
        )


class SaveMenuState(PaginatedMenuState):
    name: ClassVar[str] = "SaveMenuState"
    shrink_to_items = True

    def __init__(
        self,
        client: BaseClient,
        selected_index: int | None = None,
        **kwargs: Any,
    ):
        self.max_slots = client.config.save_slots
        self.save_slots_per_page = client.config.save_slots_per_page

        super().__init__(
            client=client, selected_index=selected_index or 0, **kwargs
        )

        self.menu_items.page_size = self.save_slots_per_page

    def initialize_items(self) -> None:
        rect = self.client.context.rect.copy()
        slot_rect = Rect(
            0,
            0,
            rect.width * SLOT_WIDTH_RATIO,
            rect.height // SLOT_HEIGHT_RATIO,
        )
        for slot in SaveManager.all_slots(
            self.max_slots, include_autosave=False
        ):
            item = self.create_menu_item(slot_rect, slot)
            self.add(item)

    def create_menu_item(self, slot_rect: Rect, slot: int) -> MenuItem[None]:
        if SaveManager.exists(slot):
            image = SaveManager.render_slot(
                slot_rect,
                slot,
                scaling=self.client.context.scaling,
                font=self.font,
            )
            return MenuItem(image, T.translate("menu_save"), None, None, True)
        else:
            image = SaveManager.render_empty(
                slot_rect,
                slot,
                scaling=self.client.context.scaling,
                font=self.font,
            )
            return MenuItem(image, T.translate("empty_slot"), None, None, True)

    def _draw_slot_text(
        self, slot_image: Surface, rect: Rect, slot: int, save_data: SaveData
    ) -> None:
        draw_text(
            slot_image,
            f"{T.translate('slot')} {slot}",
            rect,
            scaling=self.client.context.scaling,
            font=self.font,
        )

        x = int(rect.width * 0.5)
        if save_data.npc_state and save_data.npc_state.player_name:
            draw_text(
                slot_image,
                save_data.npc_state.player_name,
                (x, 0, 500, 500),
                scaling=self.client.context.scaling,
                font=self.font,
            )

        if save_data.time:
            draw_text(
                slot_image,
                save_data.time,
                (x, 50, 500, 500),
                scaling=self.client.context.scaling,
                font=self.font,
            )

    def save(self) -> None:
        self.client.event_engine.execute_action(
            "save_game",
            [self.selected_index],
            True,
        )

    def on_menu_selection(self, menuitem: MenuItem[None]) -> None:
        slot = SaveManager.slot_from_ui(self.selected_index)

        def positive() -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("SaveMenuState")
            self.save()

        def negative() -> None:
            self.client.remove_state_by_name("ChoiceState")

        def delete() -> None:
            SaveManager.delete(slot)
            self.menu_items.clear_items()
            self.reload_items()
            visible = list(self.menu_items._visible_indices())
            if visible:
                self.selected_index = visible[0]
            self.client.remove_state_by_name("ChoiceState")

        def ask() -> None:
            actions = {
                "overwrite": positive,
                "keep": negative,
                "delete": delete,
            }
            menu = MenuOptions(create_choice_options(actions))
            open_choice_dialog(self.client, menu, escape_key_exits=True)

        if SaveManager.exists(slot):
            ask()
        else:
            self.client.remove_state_by_name("SaveMenuState")
            self.save()


class LoadMenuState(PaginatedMenuState):
    name: ClassVar[str] = "LoadMenuState"
    shrink_to_items = True

    def __init__(
        self,
        client: BaseClient,
        selected_index: int | None = None,
        **kwargs: Any,
    ):
        selected_index = selected_index or 0
        self.max_slots = client.config.save_slots
        self.save_slots_per_page = client.config.save_slots_per_page

        super().__init__(
            client=client, selected_index=selected_index, **kwargs
        )
        self.menu_items.page_size = self.save_slots_per_page

    def initialize_items(self) -> None:
        rect = self.client.context.rect.copy()
        slot_rect = Rect(
            0,
            0,
            rect.width * SLOT_WIDTH_RATIO,
            rect.height // SLOT_HEIGHT_RATIO,
        )

        for slot in SaveManager.all_slots(
            self.max_slots, include_autosave=False
        ):
            item = self.create_menu_item(slot_rect, slot)
            self.add(item)

    def create_menu_item(self, slot_rect: Rect, slot: int) -> MenuItem[None]:
        if SaveManager.exists(slot):
            image = SaveManager.render_slot(
                slot_rect,
                slot,
                scaling=self.client.context.scaling,
                font=self.font,
            )
            return MenuItem(image, T.translate("menu_load"), None, None, True)
        else:
            image = SaveManager.render_empty(
                slot_rect,
                slot,
                scaling=self.client.context.scaling,
                font=self.font,
            )
            return MenuItem(
                image, T.translate("empty_slot"), None, None, False
            )

    def _draw_slot_text(
        self, slot_image: Surface, rect: Rect, slot: int, save_data: SaveData
    ) -> None:
        draw_text(
            slot_image,
            f"{T.translate('slot')} {slot}",
            rect,
            scaling=self.client.context.scaling,
            font=self.font,
        )

        x = int(rect.width * 0.5)
        if save_data.npc_state and save_data.npc_state.player_name:
            draw_text(
                slot_image,
                save_data.npc_state.player_name,
                (x, 0, 500, 500),
                scaling=self.client.context.scaling,
                font=self.font,
            )

        if save_data.time:
            draw_text(
                slot_image,
                save_data.time,
                (x, 50, 500, 500),
                scaling=self.client.context.scaling,
                font=self.font,
            )

    def on_menu_selection(self, menuitem: MenuItem[None]) -> None:
        slot = SaveManager.slot_from_ui(
            self.selected_index, includes_autosave=False
        )

        if SaveManager.exists(slot):
            self.client.event_engine.execute_action(
                "load_game",
                [slot, True],
                True,
            )
