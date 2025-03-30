# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
from base64 import b64decode
from typing import Optional

import pygame
from pygame import Rect

from tuxemon import prepare, save, tools
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.save import get_save_path
from tuxemon.session import local_session
from tuxemon.ui import text

logger = logging.getLogger(__name__)

cfgcheck = prepare.CONFIG


class SaveMenuState(PopUpMenu[None]):
    number_of_slots = 3
    shrink_to_items = True

    def __init__(self, selected_index: Optional[int] = None) -> None:
        if selected_index is None:
            selected_index = save.slot_number or 0
        super().__init__(selected_index=selected_index)

    def initialize_items(self) -> None:
        empty_image = None
        rect = self.client.screen.get_rect()
        slot_rect = Rect(0, 0, rect.width * 0.80, rect.height // 6)
        for i in range(self.number_of_slots):
            # Check to see if a save exists for the current slot
            save_path = get_save_path(i + 1)
            if os.path.exists(save_path):
                image = self.render_slot(slot_rect, i + 1)
                item = MenuItem(image, T.translate("menu_save"), None, None)
                self.add(item)
            else:
                if not empty_image:
                    empty_image = self.render_empty_slot(slot_rect)
                item = MenuItem(empty_image, "SAVE", None, None)
                self.add(item)

    def render_empty_slot(
        self,
        rect: pygame.rect.Rect,
    ) -> pygame.surface.Surface:
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)
        rect = rect.move(0, rect.height // 2 - 10)
        text.draw_text(
            slot_image,
            T.translate("empty_slot"),
            rect,
            font=self.font,
        )
        return slot_image

    def render_slot(
        self,
        rect: pygame.rect.Rect,
        slot_num: int,
    ) -> pygame.surface.Surface:
        slot_image = pygame.Surface(rect.size, pygame.SRCALPHA)

        # Try and load the save game and draw details about the save
        save_data = save.load(slot_num)
        assert save_data
        if "screenshot" in save_data:
            screenshot = b64decode(save_data["screenshot"])
            size = (
                save_data["screenshot_width"],
                save_data["screenshot_height"],
            )
            thumb_image = pygame.image.frombuffer(
                screenshot,
                size,
                "RGB",
            ).convert()
            thumb_rect = thumb_image.get_rect().fit(rect)
            thumb_image = pygame.transform.smoothscale(
                thumb_image,
                thumb_rect.size,
            )
        else:
            thumb_rect = rect.copy()
            thumb_rect.width //= 5
            thumb_image = pygame.Surface(thumb_rect.size)
            thumb_image.fill(prepare.WHITE_COLOR)

        if "error" in save_data["npc_state"]:
            red = prepare.RED_COLOR
            pygame.draw.line(thumb_image, red, [0, 0], thumb_rect.size, 3)
            pygame.draw.line(
                thumb_image,
                red,
                [0, thumb_rect.height],
                [thumb_rect.width, 0],
                3,
            )

        # Draw the screenshot
        slot_image.blit(thumb_image, (rect.width * 0.20, 0))

        # Draw the slot text
        rect = rect.move(0, rect.height // 2 - 10)
        text.draw_text(
            slot_image,
            T.translate("slot") + " " + str(slot_num),
            rect,
            font=self.font,
        )

        x = int(rect.width * 0.5)
        text.draw_text(
            slot_image,
            save_data["npc_state"]["player_name"],
            (x, 0, 500, 500),
            font=self.font,
        )
        if "error" not in save_data["npc_state"]:
            text.draw_text(
                slot_image,
                save_data["time"],
                (x, 50, 500, 500),
                font=self.font,
            )

        return slot_image

    def save(self) -> None:
        self.client.event_engine.execute_action(
            "save_game",
            [self.selected_index],
            True,
        )

    def on_menu_selection(self, menuitem: MenuItem[None]) -> None:
        def positive_answer() -> None:
            self.client.pop_state()  # close confirmation menu
            self.client.pop_state()  # close save menu

            self.save()

        def negative_answer() -> None:
            self.client.pop_state()  # close confirmation menu

        def ask_confirmation() -> None:
            # open menu to confirm the save
            var_menu = []
            _overwrite = T.translate("save_overwrite")
            var_menu.append(("overwrite", _overwrite, positive_answer))
            _keep = T.translate("save_keep")
            var_menu.append(("keep", _keep, negative_answer))
            tools.open_choice_dialog(local_session, var_menu, True)

        save_data = save.load(self.selected_index + 1)
        if save_data:
            ask_confirmation()
        else:
            self.client.pop_state()  # close save menu
            self.save()
