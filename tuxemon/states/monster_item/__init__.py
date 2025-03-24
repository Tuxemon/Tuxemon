# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.states.items.item_menu import ItemMenuState


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class MonsterItemState(PygameMenuState):
    """
    Shows details of the single monster held item.
    """

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monster: Monster,
    ) -> None:

        def add_item() -> None:
            menu = self.client.push_state(ItemMenuState())
            menu.is_valid_entry = validate  # type: ignore[assignment]
            menu.on_menu_selection = choose_target  # type: ignore[method-assign]

        def validate(item: Optional[Item]) -> bool:
            return item is not None and item.behaviors.holdable

        def choose_target(menu_item: MenuItem[Item]) -> None:
            item = menu_item.game_object
            monster.held_item.set_item(item)
            assert monster.owner
            monster.owner.remove_item(item)
            self.client.remove_state_by_name("ItemMenuState")
            self.client.remove_state_by_name("MonsterItemState")
            self.client.remove_state_by_name("MonsterMenuState")

        def remove_item() -> None:
            item = monster.held_item.get_item()
            if item is not None:
                assert monster.owner
                monster.owner.add_item(item)
            monster.held_item.clear_item()
            self.client.remove_state_by_name("MonsterItemState")
            self.client.remove_state_by_name("MonsterMenuState")

        held_item = monster.held_item.get_item()

        if held_item is None:
            held = T.translate("no_held_item")
            label = f"{monster.name}: {held}"
        else:
            label = f"{monster.name}: {held_item.name}"
            new_image = self._create_image(held_item.sprite)
            new_image.scale(prepare.SCALE / 2, prepare.SCALE / 2)
            menu.add.image(
                image_path=new_image.copy(), align=locals.ALIGN_CENTER
            )
        menu.add.label(
            title=label,
            font_size=self.font_size_small,
            align=locals.ALIGN_CENTER,
        )
        if held_item is not None:
            menu.add.label(
                title=held_item.description,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                wordwrap=True,
            )
            menu.add.button(
                title=T.translate("generic_remove"),
                action=remove_item,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
            )
        else:
            assert monster.owner
            holdable = [
                item for item in monster.owner.items if item.behaviors.holdable
            ]
            if holdable:
                menu.add.button(
                    title=T.translate("generic_add"),
                    action=add_item,
                    font_size=self.font_size_small,
                    align=locals.ALIGN_CENTER,
                )

    def __init__(self, **kwargs: Any) -> None:
        monster: Optional[Monster] = None
        source = ""
        for element in kwargs.values():
            monster = element["monster"]
            source = element["source"]
        if monster is None:
            raise ValueError("No monster")
        width, height = prepare.SCREEN_SIZE

        super().__init__(height=height, width=width)
        self._source = source
        self._monster = monster
        self.add_menu_items(self.menu, monster)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        param: dict[str, Any] = {"source": self._source}
        client = self.client

        if self._source in [
            "WorldMenuState",
            "MonsterMenuState",
            "MonsterTakeState",
        ]:
            monsters = self._get_monsters()
            slot = monsters.index(self._monster)

            if event.button == buttons.RIGHT and event.pressed:
                slot = (slot + 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterItemState", kwargs=param)
            elif event.button == buttons.LEFT and event.pressed:
                slot = (slot - 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterItemState", kwargs=param)

        if event.button in (buttons.BACK, buttons.B) and event.pressed:
            client.pop_state()
        elif event.button == buttons.A and event.pressed:
            return super().process_event(event)
        return None

    def _get_monsters(self) -> list[Monster]:
        if self._source == "MonsterTakeState":
            box = local_session.player.monster_boxes.get_box_name(
                self._monster.instance_id
            )
            if box is None:
                raise ValueError("Box doesn't exist")
            return local_session.player.monster_boxes.get_monsters(box)
        else:
            return local_session.player.monsters

    def update_animation_size(self) -> None:
        widgets_size = self.menu.get_size(widget=True)
        self.menu.resize(
            max(1, int(widgets_size[0] * self.animation_size)),
            max(1, int(widgets_size[1] * self.animation_size)),
        )

    def animate_open(self) -> Animation:
        """
        Animate the menu popping in.

        Returns:
            Popping in animation.

        """
        self.animation_size = 0.0
        ani = self.animate(self, animation_size=1.0, duration=0.2)
        ani.update_callback = self.update_animation_size
        return ani
