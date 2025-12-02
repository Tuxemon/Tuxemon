# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, ClassVar, Optional

from pygame.rect import Rect

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.technique.controller import TechController
from tuxemon.technique.filter import TechFilter
from tuxemon.technique.sorter import TechSorter
from tuxemon.technique.technique import Technique
from tuxemon.tools import (
    open_choice_dialog,
    scale,
)
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.npc import NPC


class TechniqueMenuState(Menu[Technique]):
    """The technique menu allows you to view and use techniques of your party."""

    name: ClassVar[str] = "TechniqueMenuState"
    background_filename = prepare.BG_MOVES
    draw_borders = False

    def __init__(
        self,
        character: NPC,
        techniques: list[Technique],
        tech_filter: Optional[TechFilter] = None,
        tech_sorter: Optional[TechSorter] = None,
    ) -> None:
        self.char = character
        self.tech_filter = tech_filter or TechFilter(techniques)
        self.tech_sorter = tech_sorter or TechSorter()

        super().__init__()

        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.technique_sprite = Sprite()
        self.sprites.add(self.technique_sprite)
        self.menu_items.line_spacing = scale(7)

        # this is the area where the technique description is displayed
        rect = prepare.SCREEN_RECT.copy()
        rect.top = scale(106)
        rect.left = scale(3)
        rect.width = scale(250)
        rect.height = scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

    def calc_internal_rect(self) -> Rect:
        # area in the screen where the technique list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def on_menu_selection(self, menu_technique: MenuItem[Technique]) -> None:
        """
        Called when player has selected something from the moves.
        """
        tech = menu_technique.game_object

        # Condition 1: is this technique valid for at least one monster?
        valid_for_monster = any(
            tech.validate_monster(local_session, m) for m in self.char.monsters
        )

        # Condition 2: can this technique be used in the current field context?
        usable_in_field = tech.behaviors.is_field_tech

        is_usable = valid_for_monster and usable_in_field
        self.open_confirm_use_menu(tech, is_usable)

    def open_confirm_use_menu(
        self, technique: Technique, is_usable: bool
    ) -> None:
        """
        Opens a confirmation menu for the given technique, dynamically creating options,
        and injects the menu-level 'Sort' option.
        """
        controller = TechController(local_session, technique, self.char)
        menu_options = controller.get_confirm_menu_options()

        if not is_usable:
            menu_options.remove("use")

        sort_option = ChoiceOption(
            key="sort",
            display_text=T.translate("menu_sort").upper(),
            action=self.open_sort_submenu,
        )

        last_index = len(menu_options.options) - 1
        if last_index >= 0 and menu_options.options[last_index].key in (
            "cancel",
            "back",
            "close",
        ):
            menu_options.options.insert(last_index, sort_option)
        else:
            menu_options.options.append(sort_option)

        open_choice_dialog(self.client, menu_options, escape_key_exits=True)

    def initialize_items(
        self,
    ) -> Generator[MenuItem[Technique], None, None]:
        """Get all player techniques."""
        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45

        output = self.tech_filter.get_filtered_techniques()
        if not output:
            return

        for tech in self.tech_sorter.sort(output):
            mon = self.char.party.find_monster_by_tech_id(tech.instance_id)
            if mon:
                sprite = mon.sprite_handler.front_path
            else:
                sprite = prepare.MISSING_IMAGE
            self.load_sprite(
                sprite,
                center=self.backpack_center,
                layer=100,
            )
            yield self.create_technique_menu_item(tech)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        technique = self.get_selected_item()
        # show technique description
        if technique:
            if technique.description:
                self.dialog.alert(
                    technique.description, self.text_area, dialog_speed="max"
                )

    def is_valid_entry(self, technique: Optional[Technique]) -> bool:
        """
        Used to determine if a given technique should be selectable.
        """
        return technique is not None

    def create_technique_menu_item(
        self, tech: Technique
    ) -> MenuItem[Technique]:
        name = tech.name
        types = " ".join(s.name for s in tech.types.current)
        image = self.shadow_text(name, bg=prepare.DIMGRAY_COLOR)
        label = T.format(
            "technique_description",
            {
                "id": tech.tech_id,
                "types": types,
                "acc": int(tech.accuracy * 100),
                "pot": int(tech.potency * 100),
                "pow": tech.power,
                "rec": str(tech.recharge_length),
            },
        )
        if tech.description and tech.description != f"{tech.slug}_description":
            label = f"{label} - {tech.description}"
        return MenuItem(image, name, label, tech)

    def set_sort_mode(self, mode: str) -> None:
        """Change the sorting mode and reload the inventory."""
        self.tech_sorter.set_mode(mode)
        self.reload_items()

    def open_sort_submenu(self) -> None:
        """Opens a submenu with sorting options for items."""
        sort_options = [
            ChoiceOption(
                key="id",
                display_text=T.translate("sort_by_id").upper(),
                action=lambda: self.set_sort_mode("id"),
            ),
            ChoiceOption(
                key="name",
                display_text=T.translate("sort_by_name").upper(),
                action=lambda: self.set_sort_mode("name"),
            ),
            ChoiceOption(
                key="power",
                display_text=T.translate("sort_by_power").upper(),
                action=lambda: self.set_sort_mode("power"),
            ),
        ]
        menu = MenuOptions(sort_options)
        open_choice_dialog(self.client, menu, escape_key_exits=True)
