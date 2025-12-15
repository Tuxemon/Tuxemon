# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from base64 import b64decode
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional

from pygame import SRCALPHA
from pygame.image import frombuffer
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.transform import smoothscale

from tuxemon import prepare, save
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.save import get_save_path
from tuxemon.tools import open_choice_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions
from tuxemon.ui.text import draw_text

if TYPE_CHECKING:
    from tuxemon.save_state import SaveData

logger = logging.getLogger(__name__)


SLOT_WIDTH_RATIO = 0.80
SLOT_HEIGHT_RATIO = 6


class SaveMenuState(PopUpMenu[None]):
    name: ClassVar[str] = "SaveMenuState"
    number_of_slots = 3
    shrink_to_items = True

    def __init__(self, selected_index: Optional[int] = None) -> None:
        if selected_index is None:
            selected_index = save.slot_number or 0
        super().__init__(selected_index=selected_index)

    def create_menu_item(
        self, slot_rect: Rect, slot_index: int, selectable: bool = True
    ) -> MenuItem[None]:
        save_path = Path(get_save_path(slot_index))

        if save_path.exists():
            image = self.render_slot(slot_rect, slot_index)
            return MenuItem(image, T.translate("menu_save"), None, None, True)
        else:
            empty_image = self.render_empty_slot(slot_rect)
            return MenuItem(
                empty_image, T.translate("empty_slot"), None, None, selectable
            )

    def initialize_items(self) -> None:
        rect = prepare.SCREEN_RECT.copy()
        slot_rect = Rect(
            0,
            0,
            rect.width * SLOT_WIDTH_RATIO,
            rect.height // SLOT_HEIGHT_RATIO,
        )
        for i in range(self.number_of_slots):
            item = self.create_menu_item(slot_rect, i + 1)
            self.add(item)

    def render_empty_slot(self, rect: Rect) -> Surface:
        slot_image = Surface(rect.size, SRCALPHA)
        rect = rect.move(0, rect.height // 2 - 10)
        draw_text(
            slot_image,
            T.translate("empty_slot"),
            rect,
            font=self.font,
        )
        return slot_image

    def render_slot(self, rect: Rect, slot_num: int) -> Surface:
        slot_image = Surface(rect.size, SRCALPHA)

        # Load the save data
        save_path = save.get_save_path(slot_num)
        save_data = save.load(save_path)
        if not save_data:
            logger.critical(f"Save data not found for slot {slot_num}.")
            raise RuntimeError(
                f"Critical error: Save data missing for slot {slot_num}"
            )

        # Draw the thumbnail
        thumb_image = self._get_thumbnail(save_data, rect)
        slot_image.blit(thumb_image, (rect.width * 0.20, 0))

        # Draw the slot text
        rect = rect.move(0, rect.height // 2 - 10)
        self._draw_slot_text(slot_image, rect, slot_num, save_data)

        return slot_image

    def _get_thumbnail(self, save_data: SaveData, rect: Rect) -> Surface:
        if (
            save_data.screenshot is not None
            and save_data.screenshot_width is not None
            and save_data.screenshot_height is not None
        ):
            screenshot = b64decode(save_data.screenshot)
            size = (save_data.screenshot_width, save_data.screenshot_height)
            thumb_image = frombuffer(screenshot, size, "RGB").convert()
            thumb_rect = thumb_image.get_rect().fit(rect)
            return smoothscale(thumb_image, thumb_rect.size)

        # Fallback thumbnail if screenshot data is missing or incomplete
        thumb_rect = rect.copy()
        thumb_rect.width //= 5
        thumb_image = Surface(thumb_rect.size)
        thumb_image.fill(prepare.WHITE_COLOR)
        return thumb_image

    def _draw_slot_text(
        self,
        slot_image: Surface,
        rect: Rect,
        slot_num: int,
        save_data: SaveData,
    ) -> None:
        draw_text(
            slot_image,
            f"{T.translate('slot')} {slot_num}",
            rect,
            font=self.font,
        )

        x = int(rect.width * 0.5)
        if save_data.npc_state and save_data.npc_state.player_name:
            draw_text(
                slot_image,
                save_data.npc_state.player_name,
                (x, 0, 500, 500),
                font=self.font,
            )
        if save_data.time:
            draw_text(
                slot_image,
                save_data.time,
                (x, 50, 500, 500),
                font=self.font,
            )

    def save(self) -> None:
        self.client.event_engine.execute_action(
            "save_game",
            [self.selected_index],
            True,
        )

    def on_menu_selection(self, menuitem: MenuItem[None]) -> None:
        def positive_answer() -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("SaveMenuState")

            self.save()

        def negative_answer() -> None:
            self.client.remove_state_by_name("ChoiceState")

        def delete_answer() -> None:
            slot = self.selected_index + 1
            delete_save_slot(slot)
            self.menu_items.clear()
            self.reload_items()
            self.client.remove_state_by_name("ChoiceState")

        def ask_confirmation() -> None:
            # Open menu to confirm the save
            options = [
                ChoiceOption(
                    key="overwrite",
                    display_text=T.translate("save_overwrite"),
                    action=positive_answer,
                ),
                ChoiceOption(
                    key="keep",
                    display_text=T.translate("save_keep"),
                    action=negative_answer,
                ),
                ChoiceOption(
                    key="delete",
                    display_text=T.translate("save_delete"),
                    action=delete_answer,
                ),
            ]

            menu = MenuOptions(options)
            open_choice_dialog(self.client, menu, escape_key_exits=True)

        save_path = save.get_save_path(self.selected_index + 1)
        save_data = save.load(save_path)
        if save_data:
            ask_confirmation()
        else:
            self.client.remove_state_by_name("SaveMenuState")
            self.save()


def delete_save_slot(slot_num: int) -> bool:
    """
    Deletes the save file for the given slot number.

    Parameters:
        slot_num: The slot number of the save to delete.

    Returns:
        bool: True if the save file was deleted successfully, False otherwise.
    """
    save_path = Path(get_save_path(slot_num))

    if save_path.exists():
        try:
            save_path.unlink()
            logger.info(
                f"Save slot {slot_num} deleted successfully at path {save_path}."
            )
            return True
        except OSError as e:
            logger.error(
                f"Failed to delete save slot {slot_num} at path {save_path}. Error: {e}"
            )
            return False
    else:
        logger.warning(
            f"Save slot {slot_num} does not exist at path {save_path}."
        )
        return False
