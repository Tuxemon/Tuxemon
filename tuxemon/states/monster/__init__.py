# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from typing import Optional

from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare, tools
from tuxemon.graphics import ColorLike, load_and_scale, load_image
from tuxemon.locale import T
from tuxemon.menu.interface import ExpBar, HpBar, MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster import Monster
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea, draw_text


class MonsterMenuState(Menu[Optional[Monster]]):
    """
    A class to create monster menu objects.

    The monster menu allows you to view monsters in your party,
    teach them moves, and switch them both in and out of combat.
    """

    background_filename = prepare.BG_MONSTERS
    draw_borders = False

    def __init__(self) -> None:
        super().__init__()

        # make a text area to show messages
        self.text_area = TextArea(self.font, self.font_color, (96, 96, 96))
        self.text_area.rect = Rect(tools.scale_sequence((20, 80, 80, 100)))
        self.sprites.add(self.text_area, layer=100)
        self.held_item_display = HeldItemDisplay(self)
        self.monster_sprite_displays: list[MonsterSpriteDisplay] = []
        self.monster_sprite_display = MonsterSpriteDisplay(self)
        self.monster_portrait_display = MonsterPortraitDisplay(self)

        # Set up the border images used for the monster slots
        self.hp_bar = HpBar()
        self.exp_bar = ExpBar()
        self.monster_info_renderer = MonsterInfoRenderer(
            self.font, self.hp_bar, self.font_color
        )
        self.monster_slot_border = MonsterSlotBorder()

        # TODO: something better than this global, load_sprites stuff
        for monster in local_session.player.monsters:
            monster.load_sprites()

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
            self.monster_portrait_display.update(monster)
        except IndexError:
            self.monster_portrait_display.update(None)

        self.animations.empty()
        self.monster_portrait_display.animate_down()

        # position and animate the monster portrait
        width = prepare.SCREEN_SIZE[0] // 2
        height = prepare.SCREEN_SIZE[1] // int(
            local_session.player.party_limit * 1.5,
        )

        # make 6 slots
        for _ in range(local_session.player.party_limit):
            rect = Rect(0, 0, width, height)
            surface = Surface(rect.size, SRCALPHA)
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
        surface: Surface,
        rect: Rect,
        monster: Optional[Monster],
        in_focus: bool,
    ) -> Surface:
        filled = monster is not None
        border = self.monster_slot_border.get_border(in_focus, filled)
        border.draw(surface)
        if monster is not None:
            self.draw_monster_info(surface, monster, rect)
        return surface

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        """
        Used to determine if a given monster should be selectable.

        When other code creates a MonsterMenu, it should overwrite this method
        to suit its needs.

        Parameters:
            monster: The monster corresponding to the menu item, if any.
        """
        return monster is not None

    def refresh_menu_items(self) -> None:
        """Used to render slots after their 'focus' flags change."""
        self.monster_sprite_displays = []

        for index, item in enumerate(self.menu_items):
            monster: Optional[Monster]
            try:
                monster = local_session.player.monsters[index]
            except IndexError:
                monster = None
            item.game_object = monster

            item.enabled = (monster is not None) and self.is_valid_entry(
                item.game_object
            )
            item.image.fill(prepare.TRANSPARENT_COLOR)
            item.in_focus = (index == self.selected_index) and item.enabled
            self.render_monster_slot(
                item.image,
                item.image.get_rect(),
                item.game_object,
                item.in_focus,
            )
            if monster:
                monster_sprite_display = MonsterSpriteDisplay(self)
                monster_sprite_display.update(monster, item.rect)
                self.monster_sprite_displays.append(monster_sprite_display)

    def draw_monster_info(
        self,
        surface: Surface,
        monster: Monster,
        rect: Rect,
    ) -> None:
        self.monster_info_renderer.draw(surface, monster, rect)

    def on_menu_selection_change(self) -> None:
        try:
            monster = local_session.player.monsters[self.selected_index]
            self.monster_portrait_display.update(monster)
        except IndexError:
            self.monster_portrait_display.update(None)
        self.held_item_display.update(monster)
        self.refresh_menu_items()

    def remove_monster_sprite_display(self, monster: Monster) -> None:
        for sprite_display in self.monster_sprite_displays:
            if sprite_display.monster == monster:
                if sprite_display.sprite:
                    self.sprites.remove(sprite_display.sprite)
                self.monster_sprite_displays.remove(sprite_display)
                break


class HeldItemDisplay:
    def __init__(self, menu_state: MonsterMenuState) -> None:
        self.menu_state = menu_state
        self.sprite = TextArea(
            self.menu_state.font, self.menu_state.font_color
        )
        self.menu_state.sprites.add(self.sprite)

    def update(self, monster: Optional[Monster]) -> None:
        text = ""
        if monster:
            stats = [
                (
                    T.translate("short_hp"),
                    f"{monster.current_hp}/{monster.hp}",
                ),
                (T.translate("armour"), monster.armour),
                (T.translate("dodge"), monster.dodge),
                (T.translate("melee"), monster.melee),
                (T.translate("ranged"), monster.ranged),
                (T.translate("speed"), monster.speed),
            ]
            if monster.held_item.item:
                stats.append((T.translate("menu_item"), T.translate("yes")))
            else:
                stats.append((T.translate("menu_item"), T.translate("no")))

            max_len = max(len(stat[0]) for stat in stats)
            for stat in stats:
                text += f"{stat[0]:<{max_len}}: {stat[1]}\n"
        image = self.menu_state.shadow_text(text)
        self.sprite.image = image
        width, height = prepare.SCREEN_SIZE
        self.sprite.rect.topleft = (width // 10, height // 2 + 50)


class MonsterSpriteDisplay:
    def __init__(self, menu_state: MonsterMenuState) -> None:
        self.menu_state = menu_state
        self.sprite: Optional[Sprite] = None
        self.monster: Optional[Monster] = None

    def update(self, monster: Optional[Monster], rect: Rect) -> None:
        self.monster = monster
        if monster:
            if self.sprite is None:
                self.sprite = monster.get_sprite("menu", 0.25, 2.5)
                self.menu_state.sprites.add(self.sprite)
            if self.sprite is not None:
                self.sprite.rect.x = prepare.SCREEN_SIZE[0] - (
                    self.sprite.rect.width
                    + int(prepare.SCREEN_SIZE[0] * 0.005)
                )
                self.sprite.rect.y = rect.y + (self.sprite.rect.height)
        else:
            if self.sprite is not None:
                self.menu_state.sprites.remove(self.sprite)
                self.sprite = None


class MonsterPortraitDisplay:
    def __init__(self, menu_state: MonsterMenuState) -> None:
        self.menu_state = menu_state
        self.portrait = Sprite()
        self.portrait.rect = Rect(0, 0, 0, 0)
        self.menu_state.sprites.add(self.portrait)

    def update(self, monster: Optional[Monster]) -> None:
        image = None
        if monster is not None:
            try:
                sprite = monster.get_sprite("front")
                image = sprite.image
            except AttributeError:
                pass
        image = image or Surface((1, 1), SRCALPHA)

        self.portrait.image = image
        width, height = prepare.SCREEN_SIZE
        self.portrait.rect = image.get_rect(
            centerx=width // 4,
            top=height // 12,
        )

    def animate_down(self) -> None:
        ani = self.menu_state.animate(
            self.portrait.rect,
            y=-tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.callback = self.animate_up

    def animate_up(self) -> None:
        ani = self.menu_state.animate(
            self.portrait.rect,
            y=tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.callback = self.animate_down


class MonsterInfoRenderer:
    def __init__(
        self, font: Font, hp_bar: HpBar, font_color: ColorLike
    ) -> None:
        self.font = font
        self.hp_bar = hp_bar
        self.font_color = font_color

    def draw_hp_bar(
        self, surface: Surface, monster: Monster, rect: Rect
    ) -> None:
        hp_rect = rect.copy()
        left = int(rect.width * 0.6)
        right = rect.right - tools.scale(4)
        hp_rect.width = right - left
        hp_rect.left = left
        hp_rect.height = tools.scale(8)
        hp_rect.centery = rect.centery
        self.hp_bar.value = monster.current_hp / monster.hp
        self.hp_bar.draw(surface, hp_rect)

    def draw_name_and_level(
        self, surface: Surface, monster: Monster, rect: Rect
    ) -> None:
        if monster.gender == "male":
            icon = "♂"
        elif monster.gender == "female":
            icon = "♀"
        else:
            icon = ""
        upper_label = f"{monster.name}{icon}"
        text_rect = rect.inflate(-tools.scale(6), -tools.scale(6))
        draw_text(surface, upper_label, text_rect, font=self.font)
        text_rect.top = rect.bottom - tools.scale(7)
        bottom_label = f"  Lv {monster.level}"
        draw_text(surface, bottom_label, text_rect, font=self.font)

    def draw_status_icons(
        self, surface: Surface, monster: Monster, rect: Rect
    ) -> None:
        for index, status in enumerate(monster.status):
            if status.icon:
                image = load_and_scale(status.icon)
                pos = (
                    (rect.width * 0.45) + (index * tools.scale(6)),
                    rect.y + tools.scale(4),
                )
                surface.blit(image, pos)

    def draw(self, surface: Surface, monster: Monster, rect: Rect) -> None:
        self.draw_hp_bar(surface, monster, rect)
        self.draw_name_and_level(surface, monster, rect)
        self.draw_status_icons(surface, monster, rect)


class MonsterSlotBorder:
    def __init__(self, root: str = "gfx/ui/monster/"):
        self.border_types = ["empty", "filled", "active"]
        self.borders: dict[str, GraphicBox] = {}
        self.load_borders(root)

    def load_borders(self, root: str) -> None:
        for border_type in self.border_types:
            filename = root + border_type + "_monster_slot_border.png"
            border = load_and_scale(filename)

            filename = root + border_type + "_monster_slot_bg.png"
            background = load_image(filename)

            window = GraphicBox(border, background, None)
            self.borders[border_type] = window

    def get_border(self, selected: bool, filled: bool) -> GraphicBox:
        if selected:
            return self.borders["active"]
        elif filled:
            return self.borders["filled"]
        else:
            return self.borders["empty"]
