from __future__ import annotations

import uuid
from typing import Any, Generator

import pygame

from tuxemon import tools
from tuxemon.locale import T
from tuxemon.menu.interface import MenuTechnique
from tuxemon.menu.menu import Menu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.states.monster import MonsterMenuState
from tuxemon.technique.technique import Technique
from tuxemon.ui.text import TextArea


class TechniqueMenuState(Menu[Technique]):
    """The technique menu allows you to view and use techniques of your party."""

    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs: Any) -> None:
        self.state = "normal"

        self.item_center = self.rect.width * 0.164, self.rect.height * 0.13
        self.technique_sprite = Sprite()
        self.sprites.add(self.technique_sprite)

        # do not move this line
        super().startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the technique description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

    def calc_internal_rect(self) -> pygame.rect.Rect:
        # area in the screen where the technique list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def on_menu_selection(
        self, menu_technique: MenuTechnique[Technique]
    ) -> None:
        """
        Called when player has selected something.

        Currently, opens a new menu depending on the state context.

        Parameters:
            menu_technique: Selected menu technique.

        """
        tech = menu_technique.game_object

        if not any(
            menu_technique.game_object.validate(m)
            for m in local_session.player.monsters
        ):
            msg = T.format("item_no_available_target", {"name": tech.name})
            tools.open_dialog(local_session, [msg])
        elif tech.usable_in is False:
            msg = T.format("item_cannot_use_here", {"name": tech.name})
            tools.open_dialog(local_session, [msg])
        else:
            self.open_confirm_use_menu(tech)

    def open_confirm_use_menu(self, technique: Technique) -> None:
        """
        Confirm if player wants to use this technique, or not.

        Parameters:
            technique: Selected technique.

        """

        def use_technique(menu_technique: MenuTechnique[Monster]) -> None:
            monster = menu_technique.game_object

            result = technique.use(monster, monster)
            self.client.pop_state()  # pop the monster screen
            self.client.pop_state()  # pop the technique screen
            tools.show_technique_result_as_dialog(
                local_session, technique, result
            )

        def confirm() -> None:
            self.client.pop_state()  # close the confirm dialog

            menu = self.client.push_state(MonsterMenuState)
            menu.is_valid_entry = technique.validate  # type: ignore[assignment]
            menu.on_menu_selection = use_technique  # type: ignore[assignment]

        def cancel() -> None:
            self.client.pop_state()  # close the use/cancel menu

        def open_choice_menu() -> None:
            # open the menu for use/cancel
            menu = self.client.push_state(Menu)
            menu.shrink_to_items = True

            menu_techniques_map = (
                ("item_confirm_use", confirm),
                ("item_confirm_cancel", cancel),
            )

            # add our options to the menu
            for key, callback in menu_techniques_map:
                label = T.translate(key).upper()
                image = self.shadow_text(label)
                technique = MenuTechnique(image, label, None, callback)
                menu.add(technique)

        open_choice_menu()

    def initialize_items(
        self,
    ) -> Generator[MenuTechnique[Technique], None, None]:
        """Get all player techniques, remove duplicates, sort
        and add them to menu."""
        trainer = local_session.player
        mon_id = uuid.UUID(trainer.game_variables["open_monster_techs"])
        monster = trainer.find_monster_by_id(mon_id)

        # load the backpack icon
        self.backpack_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.load_sprite(
            "gfx/sprites/battle/" + monster.slug + "-front.png",
            center=self.backpack_center,
            layer=100,
        )

        moveset = []
        for moves in monster.moves:
            moveset.insert(moves.tech_id, moves.slug)

        output = sorted(moveset)
        for tech in output:
            obj = Technique(tech)
            type2 = ""
            if obj.type2 is not None:
                type2 = T.translate(obj.type2)
            image = self.shadow_text(obj.name, bg=(128, 128, 128))
            label = (
                "ID: "
                + str(obj.tech_id)
                + " - "
                + obj.name
                + " ("
                + T.translate(obj.type1)
                + type2
                + ")"
            )
            yield MenuTechnique(image, obj.name, label, obj)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        technique = self.get_selected_technique()
        # show technique description
        self.alert(technique.description)
