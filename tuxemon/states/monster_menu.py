# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Generator
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import prepare, tools
from tuxemon.animation import ScheduleType
from tuxemon.graphics import ColorLike, load_and_scale, load_image
from tuxemon.locale import T
from tuxemon.menu.interface import ExpBar, HpBar, MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster import Monster
from tuxemon.monster_dir.filter import MonsterFilter
from tuxemon.sprite import Sprite
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions
from tuxemon.ui.text import TextArea, draw_text

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


class MonsterMenuState(Menu[Optional[Monster]]):
    """
    A class to create monster menu objects.

    The monster menu allows you to view monsters in your party,
    teach them moves, and switch them both in and out of combat.
    """

    background_filename = prepare.BG_MONSTERS
    draw_borders = False

    name: ClassVar[str] = "MonsterMenuState"

    def __init__(
        self,
        monsters: list[Monster],
        monster_filter: Optional[MonsterFilter] = None,
    ) -> None:
        super().__init__()
        self.monster_filter = monster_filter or MonsterFilter()
        self.monsters = self.monster_filter.get_filtered_monsters(monsters)

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

        # Load monster visuals
        for monster in self.monsters:
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
            monster = self.monsters[self.selected_index]
            self.monster_portrait_display.update(monster)
        except IndexError:
            self.monster_portrait_display.update(None)

        self.animations.empty()
        self.monster_portrait_display.animate_down()

        # position and animate the monster portrait
        width = prepare.SCREEN_SIZE[0] // 2
        height = prepare.SCREEN_SIZE[1] // int(prepare.PARTY_LIMIT * 1.5)

        # make 6 slots
        for _ in range(prepare.PARTY_LIMIT):
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
                monster = self.monsters[index]
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
            monster = self.monsters[self.selected_index]
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


class MonsterMenuHandler:
    """Handles interactions within the monster menu."""

    def __init__(self, client: LocalPygameClient, character: NPC) -> None:
        """Initialize with client and character."""
        self.name = "WorldMenuState"
        self.client = client
        self.char = character
        self.context: dict[str, Any] = {}

    def monster_menu_hook(self, monster_menu: MonsterMenuState) -> None:
        """Handles monster reordering."""
        monster = self.context.get("monster")
        if monster:
            monster_list = self.char.monsters
            original = monster_menu.get_selected_item()
            if original and original.game_object:
                original_monster = original.game_object
                index = monster_list.index(original_monster)
                monster_list[self.context["old_index"]] = original_monster
                monster_list[index] = self.context["monster"]
                self.context["old_index"] = index

        MonsterMenuState.on_menu_selection_change(monster_menu)

    def select_monster(self, monster: Monster) -> None:
        """Selects a monster for movement."""
        self.context["monster"] = monster
        self.context["old_index"] = self.char.monsters.index(monster)
        self.client.remove_state_by_name("ChoiceState")

    def monster_stats(self, monster: Monster) -> None:
        """Displays monster statistics."""
        self.client.remove_state_by_name("ChoiceState")
        params = {"monster": monster, "source": self.name}
        self.client.push_state("MonsterInfoState", kwargs=params)

    def monster_item(self, monster: Monster) -> None:
        """Displays monster item menu."""
        self.client.remove_state_by_name("ChoiceState")
        params = {"monster": monster, "source": self.name}
        self.client.push_state("MonsterItemState", kwargs=params)

    def monster_techs(self, monster: Monster) -> None:
        """Displays monster techniques."""
        self.client.remove_state_by_name("ChoiceState")
        params = {"monster": monster, "source": self.name}
        self.client.push_state("MonsterMovesState", kwargs=params)

    def release_monster(self, monster: Monster) -> None:
        """Shows confirmation for releasing a monster."""
        self.client.remove_state_by_name("ChoiceState")
        params = {"name": monster.name.upper()}
        msg = T.format("release_confirmation", params)
        open_dialog(self.client, [msg])
        options = [
            ChoiceOption(
                key="no",
                display_text=T.translate("no"),
                action=self.negative_answer,
            ),
            ChoiceOption(
                key="yes",
                display_text=T.translate("yes"),
                action=partial(self.positive_answer, monster),
            ),
        ]
        menu = MenuOptions(options)
        open_choice_dialog(self.client, menu, escape_key_exits=False)

    def positive_answer(self, monster: Monster) -> None:
        """Handles monster release."""
        success = self.char.party.release_monster(monster)
        if success:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("DialogState")
            params = {"name": monster.name.upper()}
            msg = T.format("tuxemon_released", params)
            open_dialog(self.client, [msg])
            self.monster_menu.remove_monster_sprite_display(monster)

            num_monsters = len(self.char.monsters)
            if self.monster_menu.selected_index >= num_monsters:
                self.monster_menu.change_selection(max(0, num_monsters - 1))

            self.monster_menu.refresh_menu_items()
            self.monster_menu.on_menu_selection_change()
        else:
            open_dialog(self.client, [T.translate("cant_release")])

    def negative_answer(self) -> None:
        """Handles rejection for releasing a monster."""
        self.client.remove_state_by_name("ChoiceState")
        self.client.remove_state_by_name("DialogState")

    def open_monster_submenu(self, monster_menu: MonsterMenuState) -> None:
        """Opens a submenu for the selected monster."""
        original = monster_menu.get_selected_item()
        if original and original.game_object:
            mon = original.game_object
            options: list[ChoiceOption] = []

            options.append(
                ChoiceOption(
                    key="info",
                    display_text=T.translate("monster_menu_info").upper(),
                    action=partial(self.monster_stats, mon),
                )
            )

            if mon.moves.moves:
                options.append(
                    ChoiceOption(
                        key="tech",
                        display_text=T.translate("monster_menu_tech").upper(),
                        action=partial(self.monster_techs, mon),
                    )
                )

            if mon.held_item.item:
                options.append(
                    ChoiceOption(
                        key="item",
                        display_text=T.translate("monster_menu_item").upper(),
                        action=partial(self.monster_item, mon),
                    )
                )

            if mon.owner and mon.owner.party.party_size > 1:
                options.append(
                    ChoiceOption(
                        key="move",
                        display_text=T.translate("monster_menu_move").upper(),
                        action=partial(self.select_monster, mon),
                    )
                )

            if mon.owner and mon.owner.party.party_size > 1:
                options.append(
                    ChoiceOption(
                        key="release",
                        display_text=T.translate(
                            "monster_menu_release"
                        ).upper(),
                        action=partial(self.release_monster, mon),
                    )
                )

            menu = MenuOptions(options)
            open_choice_dialog(self.client, menu, escape_key_exits=True)

    def handle_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
        monster_menu: MonsterMenuState,
    ) -> None:
        """Handles selection interaction for monsters."""
        if "monster" in self.context:
            del self.context["monster"]
        else:
            self.open_monster_submenu(monster_menu)

    def open_monster_menu(self) -> None:
        """Pushes the monster menu state."""
        self.monster_menu = self.client.push_state(
            MonsterMenuState(self.char.monsters)
        )
        self.monster_menu.on_menu_selection = lambda item: self.handle_selection(item, self.monster_menu)  # type: ignore[assignment]
        self.monster_menu.on_menu_selection_change = partial(self.monster_menu_hook, self.monster_menu)  # type: ignore[method-assign]


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
        ani.schedule(self.animate_up, ScheduleType.ON_FINISH)

    def animate_up(self) -> None:
        ani = self.menu_state.animate(
            self.portrait.rect,
            y=tools.scale(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.schedule(self.animate_down, ScheduleType.ON_FINISH)


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
        self.hp_bar.value = monster.hp_ratio
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
        for index, status in enumerate(monster.status.get_statuses()):
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
