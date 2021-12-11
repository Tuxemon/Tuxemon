#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Leif Theden <leif.theden@gmail.com>
# Carlos Ramos <vnmabus@gmail.com>
#
#
# states.MonsterMenuState Handles creating monster menu objects
# states.JournalMenuState Menu that shows list of all monsters
#
from __future__ import annotations
import logging
import pygame

from pygame.rect import Rect
from tuxemon import prepare, graphics
from tuxemon.locale import T
from tuxemon.db import db
from tuxemon import tools
from tuxemon.menu.interface import HpBar, ExpBar, MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import draw_text, TextArea
from typing import Any, Optional, Generator
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from math import floor
import pygame

logger = logging.getLogger(__name__)


class MonsterMenuState(Menu[Optional[Monster]]):
    """
    A class to create monster menu objects.

    The monster menu allows you to view monsters in your party,
    teach them moves, and switch them both in and out of combat.
    """

    background_filename = "gfx/ui/monster/monster_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs: Any) -> None:
        super().startup(**kwargs)

        # make a text area to show messages
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 96))
        self.text_area.rect = Rect(tools.scale_sequence((20, 80, 80, 100)))
        self.sprites.add(self.text_area, layer=100)

        # Set up the border images used for the monster slots
        self.monster_slot_border = {}
        self.monster_portrait = pygame.sprite.Sprite()
        self.hp_bar = HpBar()
        self.exp_bar = ExpBar()

        # load and scale the monster slot borders
        root = "gfx/ui/monster/"
        border_types = ["empty", "filled", "active"]
        for border_type in border_types:
            filename = root + border_type + "_monster_slot_border.png"
            border = graphics.load_and_scale(filename)

            filename = root + border_type + "_monster_slot_bg.png"
            background = graphics.load_image(filename)

            window = GraphicBox(border, background, None)
            self.monster_slot_border[border_type] = window

        # TODO: something better than this global, load_sprites stuff
        for monster in local_session.player.monsters:
            monster.load_sprites()

    def animate_monster_down(self) -> None:
        ani = self.animate(
            self.monster_portrait.rect,
            y=-tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.callback = self.animate_monster_up

    def animate_monster_up(self) -> None:
        ani = self.animate(
            self.monster_portrait.rect,
            y=tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.callback = self.animate_monster_down

    def calc_menu_items_rect(self) -> Rect:
        width, height = self.rect.size
        left = width // 2.25
        top = height // 12
        width //= 2
        return Rect(left, top, width, height - top * 2)

    def initialize_items(
        self,
    ) -> Generator[MenuItem[Optional[Monster]], None, None]:
        # position the monster portrait
        try:
            monster = local_session.player.monsters[self.selected_index]
            image = monster.sprites["front"]
        except IndexError:
            image = pygame.Surface((1, 1), pygame.SRCALPHA)

        # position and animate the monster portrait
        width, height = prepare.SCREEN_SIZE
        self.monster_portrait.rect = image.get_rect(
            centerx=width // 4,
            top=height // 12,
        )
        self.sprites.add(self.monster_portrait)
        self.animations.empty()
        self.animate_monster_down()

        width = prepare.SCREEN_SIZE[0] // 2
        height = prepare.SCREEN_SIZE[1] // int(
            local_session.player.party_limit * 1.5,
        )

        # make 6 slots
        for _ in range(local_session.player.party_limit):
            rect = Rect(0, 0, width, height)
            surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            item = MenuItem(surface, None, None, None)
            yield item

        self.refresh_menu_items()

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
    ) -> None:
        pass

    def render_monster_slot(
        self,
        surface: pygame.surface.Surface,
        rect: Rect,
        monster: Optional[Monster],
        in_focus: bool,
    ) -> pygame.surface.Surface:
        filled = monster is not None
        border = self.determine_border(in_focus, filled)
        border.draw(surface)
        if monster is not None:
            self.draw_monster_info(surface, monster, rect)
        return surface

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        """
        Used to determine if a given monster should be selectable.

        When other code creates a MonsterMenu, it should overwrite this method
        to suit it's needs.

        Parameters:
            monster: The monster corresponding to the menu item, if any.

        """
        return monster is not None

    def refresh_menu_items(self) -> None:
        """Used to render slots after their 'focus' flags change."""

        for index, item in enumerate(self.menu_items):

            monster: Optional[Monster]
            try:
                monster = local_session.player.monsters[index]
            except IndexError:
                monster = None
            item.game_object = monster

            item.enabled = (
                (monster is not None)
                and self.is_valid_entry(item.game_object)
            )
            item.image.fill((0, 0, 0, 0))
            item.in_focus = (index == self.selected_index) and item.enabled
            self.render_monster_slot(
                item.image,
                item.image.get_rect(),
                item.game_object,
                item.in_focus,
            )

    def draw_monster_info(
        self,
        surface: pygame.surface.Surface,
        monster: Monster,
        rect: Rect,
    ) -> None:
        # position and draw hp bar
        hp_rect = rect.copy()
        left = int(rect.width * 0.6)
        right = rect.right - tools.scale(4)
        hp_rect.width = right - left
        hp_rect.left = left
        hp_rect.height = tools.scale(8)
        hp_rect.centery = rect.centery

        # draw the hp bar
        self.hp_bar.value = monster.current_hp / monster.hp
        self.hp_bar.draw(surface, hp_rect)

        # draw the name
        text_rect = rect.inflate(-tools.scale(6), -tools.scale(6))
        draw_text(surface, monster.name, text_rect, font=self.font)

        # draw the level info
        text_rect.top = rect.bottom - tools.scale(7)
        draw_text(
            surface,
            "  Lv " + str(monster.level),
            text_rect,
            font=self.font,
        )

        # draw any status icons
        # TODO: caching or something, idk
        # TODO: not hardcode icon sizes
        for index, status in enumerate(monster.status):
            if status.icon:
                image = graphics.load_and_scale(status.icon)
                pos = (
                    (rect.width * 0.4) + (index * tools.scale(32)),
                    rect.y + tools.scale(5),
                )
                surface.blit(image, pos)

    def determine_border(self, selected: bool, filled: bool) -> GraphicBox:
        if selected:
            return self.monster_slot_border["active"]
        elif filled:
            return self.monster_slot_border["filled"]
        else:
            return self.monster_slot_border["empty"]

    def on_menu_selection_change(self) -> None:
        try:
            monster = local_session.player.monsters[self.selected_index]
            image = monster.sprites["front"]
        except IndexError:
            image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.monster_portrait.image = image
        self.refresh_menu_items()


class JournalMenuState(Menu[Monster]):
    """The journal menu allows you to view all monsters."""

    background_filename = "gfx/ui/item/item_menu_bg.png"
    draw_borders = False

    def startup(self, **kwargs: Any) -> None:
        self.state = "normal"

        self.monster_sprite = Sprite()
        self.sprites.add(self.monster_sprite, layer=100)

        # do not move this line
        super().startup(**kwargs)
        self.menu_items.line_spacing = tools.scale(7)

        # this is the area where the item description is displayed
        rect = self.client.screen.get_rect()
        rect.top = tools.scale(106)
        rect.left = tools.scale(3)
        rect.width = tools.scale(250)
        rect.height = tools.scale(32)
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 128))
        self.text_area.rect = rect
        self.sprites.add(self.text_area, layer=100)

        self.monster_center = self.rect.width * 0.16, self.rect.height * 0.45
        self.monsters = db.lookup_entire_table("monster")
        self.monster_index = 0
        # The number of monsters to show in the list at once
        self.monsters_to_show = 11

    def calc_internal_rect(self) -> pygame.rect.Rect:
        # area in the screen where the item list is
        rect = self.rect.copy()
        rect.width = int(rect.width * 0.58)
        rect.left = int(self.rect.width * 0.365)
        rect.top = int(rect.height * 0.05)
        rect.height = int(self.rect.height * 0.60)
        return rect

    def on_menu_selection(self, menu_item: MenuItem[Monster]) -> None:
        """
        Called when player has selected a monster.

        Currently, does nothing.

        TODO: Open a new menu that shows monster details or something.

        Parameters:
            menu_item: Selected menu monster.

        """
        monster = menu_item.game_object

    def initialize_items(self) -> Generator[MenuItem[Monster], None, None]:
        """Refresh the visible tuxemon that will appear in the list.

        We mostly want the cursor to stay where it is, and scroll the list of
        monsters, except for the beginning or end of the list.

        Therefore, scroll the list by collecting N Tuxemon that we want to
        display right now, depending on the current monster_index.

        TODO: Maybe make this more efficient in the future, rather than looping
        through every single tuxemon.

        :return: List(MenuItem)
        """
        # The monster_index will always be the first tuxemon to display at the
        # top of the list. We can assume it'll always be clamped correctly so
        # we'll never go off the end of the list.
        # TODO: This function will crash if there's less monsters than in
        # self.monsters_to_show 
        i = self.monster_index
        j = 0
        for slug, monster in self.monsters.items():
            if j >= i and j < i + self.monsters_to_show:
                # TODO: Show actual tuxemon ID, rather than this temp number
                label = "{:>3}   {}".format
                label = label(str(j + 1), T.translate(slug))
                image = self.shadow_text(label)
                desc = T.translate(slug + "_description")
                item = MenuItem(
                    image,
                    label,
                    desc,
                    db.lookup(slug, "monster")
                )
                yield item
            j += 1

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        """Override normal event handling, so we can have 100% control over the
        cursor.

        If up or down is pushed, override how cursor moves using
        change_selection(), as we want the cursor to stay where it is, and
        scroll the list of monsters instead most of the time.

        If left or right is pushed, skip backwards or forwards an entire screen.

        :type event: tuxemon.input.PlayerInput
        :rtype: Optional[input.PlayerInput]
        """
        handled_event = False

        # cursor movement
        if event.button in (buttons.UP, buttons.DOWN, buttons.LEFT, buttons.RIGHT):
            handled_event = True
            valid_change = event.pressed and self.state == "normal" and self.menu_items
            if valid_change:
                if event.button == buttons.UP or event.button == buttons.DOWN:
                    index = self.menu_items.determine_cursor_movement(self.selected_index, event)
                    if not self.selected_index == index:
                        self.change_selection(index)
                elif event.button == buttons.LEFT:
                    # Loop up an entire screen
                    for i in range(self.monsters_to_show):
                        self.change_selection(self.selected_index - 1)
                elif event.button == buttons.RIGHT:
                    # Loop down an entire screen
                    for i in range(self.monsters_to_show):
                        self.change_selection(self.selected_index + 1)

        if not handled_event:
            event = super().process_event(event)
            return event

    def change_selection(self, index: int, animate: bool = True) -> None:
        """If cursor is halfway up the screen, then keep the cursor there but
        scroll list of monsters up or down by changing monster_index, which will
        update the items when initialize_items is called.

        If we're at the start or end of the list of monsters, then the screen
        doesn't need to scroll anymore - so allow index to go up or down as
        normal.

        Assuming the halfway point is = 5, ie. 10 or 11 tuxemon are being
        displayed:
        If index = 5, then cursor is in the middle of the screen, so you're at
        monster ID's between 5 and MAX-5, and need to scroll the screen by
        changing monster_index.

        If index < 4, then you're at monster ID's 0-4 - change index as normal.
        If index > 6, then you're at monster ID's MAX-4 to MAX - change index as
        normal.

        If index < 0 or index > self.monsters_to_show -1, you've gone off the
        menu and need to loop back to the start/end of the menu.

        Assumes the index will only ever move up or down by 1 each time this is
        called, and will raise a runtime error if it doesn't.

        TODO: This function will crash if there's less than
        self.monsters_to_show monsters in the monster journal.

        :return: None
        """

        # The following code wraps the cursor around when moving from the top of
        # the screen to the bottom, or vice versa.
        if index < 0:
            index = self.monsters_to_show - 1
        if index > self.monsters_to_show - 1:
            index = 0

        # TODO: I can't explain why this code is needed, but it catches bugs
        # caused by the hacky code in process_events, when using left/right to
        # move by a screen, but across the start/end of the menu. 
        # I can't explain why it's needed but changing this even a tiny bit
        # causes bugs to appear, so be careful if changing it.
        if index == 0:
            self.monster_index = 0
            super().change_selection(index, False)
        if index == self.monsters_to_show - 1:
            self.monster_index = len(self.monsters) - self.monsters_to_show
            super().change_selection(index, False)

        # If cursor is in the middle of the screen, handle it as a special case
        # - figure out if we should scroll the screen by changing monster_index,
        # or if we're near the end of the list then don't scroll and move the
        # cursor as normal.
        halfway_point = floor(self.monsters_to_show / 2)
        if self.selected_index == halfway_point:
            if index == halfway_point + 1:
                if self.monster_index >= len(self.monsters) - self.monsters_to_show:
                    # We're near the end of the list, so change index normally
                    super().change_selection(index, False)
                else:
                    # We're between monster ID's 4 and MAX-4, so keep the index
                    # the same and just increment monster_index
                    self.monster_index += 1
                    super().change_selection(self.selected_index, False)

            elif index == halfway_point -1:
                if self.monster_index == 0:
                    # We're near the start of the list, so change index normally
                    super().change_selection(index, False)
                else:
                    # We're between monster ID's 4 and MAX-4, so keep the index
                    # the same and just increment monster_index
                    self.monster_index -= 1
                    super().change_selection(self.selected_index, False)

            else:
                raise RuntimeError(f"Index moved from 5 to non-6 or 4")

        else:
            super().change_selection(index, False)

    def on_menu_selection_change(self) -> None:
        """Called when menu selection changes."""
        self.reload_items()

        item = self.get_selected_item()
        if item:
            json_monster = item.game_object
            current_monster = Monster()
            current_monster.load_from_db(json_monster["slug"])

            image = graphics.load_and_scale(current_monster.front_battle_sprite)
            self.monster_sprite.image = image
            self.monster_sprite.rect = image.get_rect(center=self.monster_center)

            self.alert(item.description)
