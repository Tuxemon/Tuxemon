# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Optional

from pygame.rect import Rect

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.technique.controller import TechController
from tuxemon.technique.filter import TechFilter
from tuxemon.technique.technique import Technique
from tuxemon.tools import (
    open_choice_dialog,
    open_dialog,
    scale,
)
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.npc import NPC


class TechniqueMenuState(Menu[Technique]):
    """The technique menu allows you to view and use techniques of your party."""

    background_filename = prepare.BG_MOVES
    draw_borders = False

    def __init__(
        self,
        character: NPC,
        techniques: list[Technique],
        monster: Optional[Monster] = None,
        tech_filter: Optional[TechFilter] = None,
    ) -> None:
        self.char = character
        self.monster = monster
        self.tech_filter = tech_filter or TechFilter(techniques)

        super().__init__()

        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.technique_sprite = Sprite()
        self.sprites.add(self.technique_sprite)
        self.menu_items.line_spacing = scale(7)

        # this is the area where the technique description is displayed
        rect = self.client.screen.get_rect()
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
        Called when player has selected something.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_technique: Selected menu technique.
        """
        tech = menu_technique.game_object

        if not any(
            menu_technique.game_object.validate_monster(local_session, m)
            for m in self.char.monsters
        ):
            msg = T.format("item_no_available_target", {"name": tech.name})
            open_dialog(self.client, [msg])
        elif tech.usable_on is False:
            msg = T.format("item_cannot_use_here", {"name": tech.name})
            open_dialog(self.client, [msg])
        else:
            self.open_confirm_use_menu(tech)

    def open_confirm_use_menu(self, technique: Technique) -> None:
        """
        Opens a confirmation menu for the given technique, dynamically creating options.
        """
        controller = TechController(local_session, technique, self.char)
        menu_options = controller.get_confirm_menu_options()
        open_choice_dialog(self.client, menu_options, escape_key_exits=True)

    def initialize_items(
        self,
    ) -> Generator[MenuItem[Technique], None, None]:
        """Get all player techniques."""
        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45
        if self.monster:
            sprite = self.monster.sprite_handler.front_path
        else:
            sprite = prepare.MISSING_IMAGE

        self.load_sprite(
            sprite,
            center=self.backpack_center,
            layer=100,
        )

        output = self.tech_filter.get_filtered_techniques()
        if not output:
            return

        output = sorted(output, key=lambda x: x.tech_id)

        for tech in output:
            yield self.create_technique_menu_item(tech)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        technique = self.get_selected_item()
        # show technique description
        if technique:
            if technique.description:
                self.dialog.alert(technique.description, dialog_speed="max")

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
