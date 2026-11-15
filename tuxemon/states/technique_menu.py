# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any, ClassVar

from pygame.rect import Rect

from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.platform.const.graphics import (
    BG_MOVES,
    DIMGRAY_COLOR,
    MISSING_IMAGE,
)
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.technique.controller import TechController
from tuxemon.technique.filter import TechFilter
from tuxemon.technique.sorter import TechSorter
from tuxemon.technique.technique import Technique
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.text import TextArea

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC


class TechniqueMenuState(Menu[Technique]):
    """The technique menu allows you to view and use techniques of your party."""

    name: ClassVar[str] = "TechniqueMenuState"
    background_filename = BG_MOVES
    draw_borders = False

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        techniques: list[Technique],
        tech_filter: TechFilter | None = None,
        tech_sorter: TechSorter | None = None,
        on_selection: Callable[[MenuItem[Technique]], None] | None = None,
        is_valid_entry: Callable[[Technique | None], bool] | None = None,
        **kwargs: Any,
    ) -> None:
        self.char = character
        self.tech_filter = tech_filter or TechFilter(techniques)
        self.tech_sorter = tech_sorter or TechSorter()
        self._external_on_selection = on_selection
        self._external_is_valid_entry = is_valid_entry

        super().__init__(client=client, **kwargs)

        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.technique_sprite = Sprite()
        self.sprites.add(self.technique_sprite)
        self.menu_items.line_spacing = self.client.context.scaling.scale_int(7)

        # this is the area where the technique description is displayed
        rect = self.client.context.rect.copy()
        rect.top = self.client.context.scaling.scale_int(106)
        rect.left = self.client.context.scaling.scale_int(3)
        rect.width = self.client.context.scaling.scale_int(250)
        rect.height = self.client.context.scaling.scale_int(32)
        self.text_area = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=rect,
            scaling=self.client.context.scaling,
            font_shadow=(96, 96, 128),
        )
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
        if self._external_on_selection:
            return self._external_on_selection(menu_technique)

        tech = menu_technique.game_object

        if not any(
            tech.validate_monster(local_session, m) for m in self.char.monsters
        ):
            msg = T.format("item_no_available_target", {"name": tech.name})
            open_dialog(self.client, [msg])
            return

        if tech.behaviors.is_field_tech is False:
            msg = T.format("item_cannot_use_here", {"name": tech.name})
            open_dialog(self.client, [msg])
            return

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

        output = self.tech_filter.get_filtered_techniques()
        if not output:
            return

        for tech in self.tech_sorter.sort(output):
            mon = self.char.party.find_monster_by_tech_id(tech.instance_id)

            if mon:
                renderer = MonsterRenderer(mon, scale=self.factor)
                sprite = renderer.get_sprite("front")
                sprite.rect.center = self.backpack_center
                self.sprites.add(sprite, layer=100)
            else:
                self.load_sprite(
                    MISSING_IMAGE,
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

    def is_valid_entry(self, technique: Technique | None) -> bool:
        """
        Used to determine if a given technique should be selectable.
        """
        if self._external_is_valid_entry:
            return self._external_is_valid_entry(technique)
        return technique is not None

    def create_technique_menu_item(
        self, tech: Technique
    ) -> MenuItem[Technique]:
        name = tech.name
        types = " ".join(s.name for s in tech.types.current)
        image = self.shadow_text(name, bg=DIMGRAY_COLOR)
        label = T.format(
            "technique_description",
            {
                "id": tech.tech_id,
                "types": types,
                "acc": int(tech.accuracy * 100),
                "pot": int(tech.potency * 100),
                "pow": tech.power,
                "rec": str(tech.cooldown.duration),
            },
        )
        if tech.description and tech.description != f"{tech.slug}_description":
            label = f"{label} - {tech.description}"
        return MenuItem(image, name, label, tech)
