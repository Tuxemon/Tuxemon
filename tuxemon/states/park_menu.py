# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable, Generator
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect

from tuxemon.db import ItemCategory
from tuxemon.item.filter import ItemFilter
from tuxemon.item.item import Item
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PopUpMenu
from tuxemon.states.item_menu import ItemMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.states.combat_state import CombatState

logger = logging.getLogger(__name__)

MenuGameObj = Callable[[], None]


class ParkMenuKeys(Enum):
    BALL = auto()
    FOOD = auto()
    DOLL = auto()
    RUN = auto()


class MainParkMenuState(PopUpMenu[MenuGameObj]):
    """Main menu Park: ball, food, doll and run"""

    name: ClassVar[str] = "MainParkMenuState"
    escape_key_exits = False
    columns = 2

    def __init__(
        self,
        client: BaseClient,
        session: Session,
        combat: CombatState,
        character: NPC,
        monster: Monster,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, **kwargs)
        self.rect = self.calculate_menu_rectangle()
        self.session = session
        self.combat = combat
        self.character = character
        self.player = session.client.combat_session.left_player  # human
        self.enemy = session.client.combat_session.right_player  # ai
        self.monster = monster
        self.opponents = (
            session.client.combat_session.field_monsters.get_monsters(
                self.enemy
            )
        )
        if not self.client.park_session.is_active:
            raise ValueError(
                "Use the event action 'park_experience start' to enable the Park Session"
            )
        self.encounter = session.client.park_session.start_encounter(
            self.opponents[0]
        )
        self.itm_description: str | None = None
        params = {"player": self.character.name}
        message = T.format("combat_player_choice", params)
        self.event_bus.publish("combat_dialog", message=message)

    def calculate_menu_rectangle(self) -> Rect:
        rect_screen = self.client.context.rect.copy()
        menu_width = rect_screen.w // 2.5
        menu_height = rect_screen.h // 4
        rect = Rect(0, 0, menu_width, menu_height)
        rect.bottomright = rect_screen.w, rect_screen.h
        return rect

    def initialize_items(self) -> Generator[MenuItem[MenuGameObj], None, None]:
        hud = self.combat.hud_manager.get_hud(self.monster)
        if hud is None:
            return
        self.combat._update_hud_details(self.monster, hud, hud.player)

        menu_items_map = (
            (ParkMenuKeys.BALL, "menu_ball", self.throw_tuxeball),
            (ParkMenuKeys.FOOD, "menu_food", self.open_item_menu),
            (ParkMenuKeys.DOLL, "menu_doll", self.open_item_menu),
            (ParkMenuKeys.RUN, "menu_run", self.run),
        )

        for menu_key_enum, translation_key, callback in menu_items_map:
            label_base = T.translate(translation_key).upper()
            item_count = 1

            if menu_key_enum == ParkMenuKeys.FOOD:
                item_count = self.check_category("food")
            elif menu_key_enum == ParkMenuKeys.DOLL:
                item_count = self.check_category("doll")

            label = (
                f"{label_base}x{item_count}"
                if item_count > 0
                and menu_key_enum in {ParkMenuKeys.FOOD, ParkMenuKeys.DOLL}
                else label_base
            )
            is_enabled = item_count > 0 or menu_key_enum not in {
                ParkMenuKeys.FOOD,
                ParkMenuKeys.DOLL,
            }

            image = (
                self.shadow_text(label)
                if is_enabled
                else self.shadow_text(label, fg=self.unavailable_color)
            )

            menu = MenuItem(image, label, translation_key, callback)
            menu.enabled = is_enabled
            yield menu

    def run(self) -> None:
        self.event_bus.publish("clean_combat")
        self.client.combat_session.reset()

    def check_category(self, cat_slug: str) -> int:
        category = sum(
            [
                itm.quantity
                for itm in self.player.items
                if itm.category == cat_slug
            ]
        )
        return category

    def throw_tuxeball(self) -> None:
        tuxeball = self.player.bag.find_item("tuxeball_park")
        if tuxeball:
            if self.encounter.check_for_flee():
                logger.info(f"{self.encounter.monster.slug} fled!")
            else:
                self.deliver_action(tuxeball)

    def open_item_menu(self) -> None:
        """Open menu to choose item to use."""
        choice = self.get_selected_item()
        if choice:
            self.itm_description = choice.description

        def choose_item() -> None:
            items_filtered = ItemFilter(self.player.items)
            items_filtered.set_filter_combat_targets(
                self.session, self.player.monsters, self.opponents
            )
            self.client.push_state(
                ItemMenuState(
                    self.client,
                    character=self.player,
                    source=self.name,
                    item_filter=items_filtered,
                    on_selection=choose_target,
                    is_valid_entry=validate,
                )
            )

        def validate(item: Item | None) -> bool:
            """Validates if the selected item from the sub-menu is allowed."""
            ret = False
            if item:
                if self.itm_description == T.translate(
                    ParkMenuKeys.DOLL.name.lower()
                ):
                    if item.category == ItemCategory.DOLL:
                        ret = True
                elif self.itm_description == T.translate(
                    ParkMenuKeys.FOOD.name.lower()
                ):
                    if item.category == ItemCategory.FOOD:
                        ret = True
            return ret

        def choose_target(menu_item: MenuItem[Item]) -> None:
            item = menu_item.game_object
            self.deliver_action(item)
            self.client.pop_state()

        choose_item()

    def deliver_action(self, item: Item) -> None:
        enemy = self.opponents[0]

        if item.category == ItemCategory.FOOD:
            self.encounter.apply_food_effect(item)
        elif item.category == ItemCategory.DOLL:
            self.encounter.apply_doll_effect(item)

        self.client.combat_session.enqueue_action(self.player, item, enemy)
        self.client.pop_state()
