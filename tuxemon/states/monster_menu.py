# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Generator
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame import SRCALPHA
from pygame.font import Font
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.animation import ScheduleType
from tuxemon.graphics import ColorLike, load_and_scale, load_image
from tuxemon.locale.locale import T
from tuxemon.menu.interface import ExpBar, HpBar, MenuItem
from tuxemon.menu.menu import Menu
from tuxemon.monster.filter import MonsterFilter
from tuxemon.monster.monster import Monster
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.platform.const.graphics import BG_MONSTERS, TRANSPARENT_COLOR
from tuxemon.platform.const.sizes import PARTY_LIMIT
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.menu_options import (
    MenuOptions,
    create_choice_options,
    create_yes_no_options,
)
from tuxemon.ui.text import TextArea, draw_text

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.party import PartyHandler
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.prepare import DisplayContext

LAYER_MONSTER_ICONS = 20
LAYER_PORTRAIT = 30


class MonsterMenuState(Menu[Monster | None]):
    """
    A class to create monster menu objects.

    The monster menu allows you to view monsters in your party,
    teach them moves, and switch them both in and out of combat.
    """

    background_filename = BG_MONSTERS
    draw_borders = False

    name: ClassVar[str] = "MonsterMenuState"

    def __init__(
        self,
        client: BaseClient,
        monsters: list[Monster],
        monster_filter: MonsterFilter | None = None,
        *,
        on_selection: Callable[[MenuItem[Monster | None]], None] | None = None,
        is_valid_entry: Callable[[Monster | None], bool] | None = None,
        on_selection_change: Callable[[MonsterMenuState], None] | None = None,
        **kwargs: Any,
    ):
        super().__init__(client=client, **kwargs)
        self._external_on_selection = on_selection
        self._external_is_valid_entry = is_valid_entry
        self._external_on_selection_change = on_selection_change
        self.monster_filter = monster_filter or MonsterFilter()
        self.monsters = self.monster_filter.get_filtered_monsters(monsters)

        # make a text area to show messages
        rect = self.client.context.scaling.scale_tuple((20, 80, 80, 100))
        self.text_area = TextArea(
            font=self.font,
            font_color=self.font_color,
            rect=Rect(rect),
            scaling=self.client.context.scaling,
            font_shadow=(96, 96, 96),
        )
        self.sprites.add(self.text_area, layer=100)
        self.monster_stats_display = MonsterStatsDisplay(self)
        self.monster_sprite_displays: list[MonsterSpriteDisplay] = []
        self.monster_portrait_display = MonsterPortraitDisplay(self)

        # Set up the border images used for the monster slots
        self.hp_bar = HpBar(self.client.context)
        self.exp_bar = ExpBar(self.client.context)
        self.slot_renderer = MonsterSlotRenderer(
            self.client.context, self.font, self.hp_bar, self.font_color
        )

    def calc_menu_items_rect(self) -> Rect:
        width, height = self.rect.size
        left = width // 2.25
        top = height // 12
        width //= 2
        return Rect(left, top, width, height - top * 2)

    def initialize_items(
        self,
    ) -> Generator[MenuItem[Monster | None], None, None]:
        # position the monster portrait
        try:
            monster = self.monsters[self.selected_index]
            self.monster_portrait_display.update(monster)
        except IndexError:
            self.monster_portrait_display.update(None)

        self.animations.empty()
        self.monster_portrait_display.animate_down()

        # position and animate the monster portrait
        _width, _height = self.client.context.resolution
        width = _width // 2
        height = _height // int(PARTY_LIMIT * 1.5)

        # make 6 slots
        for _ in range(PARTY_LIMIT):
            rect = Rect(0, 0, width, height)
            surface = Surface(rect.size, SRCALPHA)
            item = MenuItem(surface, None, None, None)
            yield item

        self.refresh_menu_items()

    def on_menu_selection(self, item: MenuItem[Monster | None]) -> None:
        if self._external_on_selection:
            return self._external_on_selection(item)
        return None

    def is_valid_entry(self, monster: Monster | None) -> bool:
        if self._external_is_valid_entry:
            return self._external_is_valid_entry(monster)
        return monster is not None

    def refresh_menu_items(self) -> None:
        """Used to render slots after their 'focus' flags change."""
        MonsterSpriteDisplay.cleanup(self.monster_sprite_displays)

        for index, item in enumerate(self.menu_items):
            self.assign_monster_to_item(index, item)

    def assign_monster_to_item(
        self, index: int, item: MenuItem[Monster | None]
    ) -> None:
        monster = self.monsters[index] if index < len(self.monsters) else None
        item.game_object = monster
        item.enabled = (monster is not None) and self.is_valid_entry(monster)
        item.image.fill(TRANSPARENT_COLOR)
        item.in_focus = (index == self.selected_index) and item.enabled
        self.slot_renderer.render_slot(
            item.image, item.image.get_rect(), monster, item.in_focus
        )

        if monster:
            sprite_display = MonsterSpriteDisplay(self)
            sprite_display.update(monster, item.rect)
            self.monster_sprite_displays.append(sprite_display)

    def on_menu_selection_change(self) -> None:
        if self._external_on_selection_change:
            self._external_on_selection_change(self)

        monster: Monster | None = None
        try:
            monster = self.monsters[self.selected_index]
            self.monster_portrait_display.update(monster)
        except IndexError:
            self.monster_portrait_display.update(None)

        self.monster_stats_display.update(monster)
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

    def __init__(self, client: BaseClient, party: PartyHandler) -> None:
        """Initialize with client and character."""
        self.name = "WorldMenuState"
        self.client = client
        self.party = party
        self.context: dict[str, Any] = {}

    def monster_menu_hook(self, monster_menu: MonsterMenuState) -> None:
        """Handles monster reordering."""
        monster = self.context.get("monster")
        if not monster:
            return

        monster_list = self.party.monsters
        original = monster_menu.get_selected_item()
        if original and original.game_object:
            original_monster = original.game_object
            index = monster_list.index(original_monster)
            monster_list[self.context["old_index"]] = original_monster
            monster_list[index] = self.context["monster"]
            self.context["old_index"] = index

    def select_monster(self, monster: Monster) -> None:
        """Selects a monster for movement."""
        self.context["monster"] = monster
        self.context["old_index"] = self.party.monsters.index(monster)
        self.client.remove_state_by_name("ChoiceState")

    def monster_stats(self, monster: Monster) -> None:
        """Displays monster statistics."""
        self.client.remove_state_by_name("ChoiceState")
        params = {
            "monster": monster,
            "source": self.name,
            "monsters": self.party.monsters,
        }
        self.client.push_state("MonsterInfoState", **params)

    def monster_techs(self, monster: Monster) -> None:
        """Displays monster techniques."""
        self.client.remove_state_by_name("ChoiceState")
        params = {
            "monster": monster,
            "source": self.name,
            "monsters": self.party.monsters,
        }
        self.client.push_state("MonsterMovesState", **params)

    def remove_item_direct(self, monster: Monster) -> None:
        item = monster.held_item
        if item:
            monster.unequip_item()
            self.party.owner.bag.add_item(item)

        self.client.remove_state_by_name("ChoiceState")
        self.monster_menu.refresh_menu_items()

    def open_item_picker(self, monster: Monster) -> None:
        from tuxemon.item.filter import ItemFilter
        from tuxemon.states.item_menu import ItemMenuState

        self.client.remove_state_by_name("ChoiceState")
        items_filtered = ItemFilter(self.party.owner.bag.items)
        items_filtered.add_filter(lambda item: item.behaviors.holdable)
        # the picker skips the validation the item menu does for a used item,
        # so an item this monster fails the conditions for is left out here
        items_filtered.add_filter(
            lambda item: item.validate_monster(local_session, monster)
        )

        self.client.push_state(
            ItemMenuState(
                self.client,
                character=self.party.owner,
                source=self.name,
                item_filter=items_filtered,
                on_selection=lambda menu_item: self._equip_from_picker(
                    monster, menu_item
                ),
            )
        )

    def _equip_from_picker(
        self, monster: Monster, menu_item: MenuItem[Item | None]
    ) -> None:
        item = menu_item.game_object
        if not item:
            return

        result = monster.equip_item(local_session, item)
        self.client.remove_state_by_name("ItemMenuState")

        if not result:
            if result.reason:
                open_dialog(self.client, [result.reason], dialog_speed="max")
            return

        self.party.owner.bag.remove_item(item)
        self.monster_menu.refresh_menu_items()

    def swap_items(self, mon_a: Monster, mon_b: Monster) -> None:
        """Swaps held items between two monsters."""
        result = mon_a.swap_items(local_session, mon_b)
        self.client.remove_state_by_name("ChoiceState")

        if not result:
            if result.reason:
                open_dialog(self.client, [result.reason], dialog_speed="max")
            return

        self.monster_menu.refresh_menu_items()

    def open_swap_picker(self, monster: Monster) -> None:
        """Opens a submenu to choose another monster to swap items with."""
        self.client.remove_state_by_name("ChoiceState")

        candidates = [
            m for m in self.party.monsters if m is not monster and m.held_item
        ]

        if not candidates:
            return

        actions = {
            m.name: partial(self.swap_items, monster, m) for m in candidates
        }
        menu = MenuOptions(create_choice_options(actions))
        open_choice_dialog(self.client, menu, escape_key_exits=True)

    def release_monster(self, monster: Monster) -> None:
        """Shows confirmation for releasing a monster."""
        self.client.remove_state_by_name("ChoiceState")
        params = {"name": monster.name.upper()}
        msg = T.format("release_confirmation", params)
        open_dialog(self.client, [msg], dialog_speed="max")

        options = create_yes_no_options(
            yes_action=partial(self.positive_answer, monster),
            no_action=self.negative_answer,
        )

        menu = MenuOptions(options)
        open_choice_dialog(self.client, menu, escape_key_exits=False)

    def positive_answer(self, monster: Monster) -> None:
        """Handles monster release."""
        success = self.party.release_monster(monster)
        if success:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("DialogState")
            params = {"name": monster.name.upper()}
            msg = T.format("tuxemon_released", params)
            open_dialog(self.client, [msg], dialog_speed="max")
            self.monster_menu.remove_monster_sprite_display(monster)

            num_monsters = len(self.party.monsters)
            if self.monster_menu.selected_index >= num_monsters:
                self.monster_menu.change_selection(max(0, num_monsters - 1))

            self.monster_menu.refresh_menu_items()
            self.monster_menu.on_menu_selection_change()
        else:
            open_dialog(
                self.client, [T.translate("cant_release")], dialog_speed="max"
            )

    def negative_answer(self) -> None:
        """Handles rejection for releasing a monster."""
        self.client.remove_state_by_name("ChoiceState")
        self.client.remove_state_by_name("DialogState")

    def open_monster_submenu(self, monster_menu: MonsterMenuState) -> None:
        """Opens a submenu for the selected monster."""
        original = monster_menu.get_selected_item()
        if not (original and original.game_object):
            return

        mon = original.game_object

        actions: dict[str, Callable[..., None]] = {
            "info": partial(self.monster_stats, mon),
        }

        if mon.moves.moves:
            actions["tech"] = partial(self.monster_techs, mon)

        if mon.held_item:
            actions["unequip_item"] = partial(self.remove_item_direct, mon)

        holdable_items = [
            item
            for item in self.party.owner.bag.items
            if item.behaviors.holdable
        ]

        if holdable_items:
            actions["equip_item"] = partial(self.open_item_picker, mon)

        other_with_items = [
            m for m in self.party.monsters if m is not mon and m.held_item
        ]

        if other_with_items:
            actions["swap_item"] = partial(self.open_swap_picker, mon)

        if self.party.party_size > 1:
            actions.update(
                {
                    "move": partial(self.select_monster, mon),
                    "sort": lambda: self.open_sort_submenu(monster_menu),
                    "release": partial(self.release_monster, mon),
                }
            )

        options = create_choice_options(actions)
        menu = MenuOptions(options)
        open_choice_dialog(self.client, menu, escape_key_exits=True)

    def handle_selection(
        self,
        menu_item: MenuItem[Monster | None],
        monster_menu: MonsterMenuState,
    ) -> None:
        """Handles selection interaction for monsters."""
        if "monster" in self.context:
            del self.context["monster"]
        else:
            self.open_monster_submenu(monster_menu)

    def sort_monsters(
        self,
        monster_menu: MonsterMenuState,
        key: Callable[[Monster], Any],
        reverse: bool = False,
    ) -> None:
        """Sorts the monsters in the party by a given key."""
        self.party.monsters.sort(key=key, reverse=reverse)
        monster_menu.monsters = self.party.monsters
        monster_menu.refresh_menu_items()
        monster_menu.on_menu_selection_change()

    def open_monster_menu(self) -> None:
        """Pushes the monster menu state."""
        self.monster_menu = self.client.push_state(
            MonsterMenuState(
                self.client,
                self.party.monsters,
                on_selection=lambda item: self.handle_selection(
                    item, self.monster_menu
                ),
                on_selection_change=self.monster_menu_hook,
            )
        )

    def open_sort_submenu(self, monster_menu: MonsterMenuState) -> None:
        """Opens a submenu with sorting options."""
        actions: dict[str, Callable[..., None]] = {
            "level": lambda: self.sort_monsters(
                monster_menu, key=lambda m: m.level
            ),
            "hp": lambda: self.sort_monsters(
                monster_menu, key=lambda m: m.hp_ratio, reverse=True
            ),
            "name": lambda: self.sort_monsters(
                monster_menu, key=lambda m: m.name.lower()
            ),
            "id": lambda: self.sort_monsters(
                monster_menu, key=lambda m: m.txmn_id
            ),
        }
        options = create_choice_options(actions)
        menu = MenuOptions(options)
        open_choice_dialog(self.client, menu, escape_key_exits=True)


class MonsterStatsDisplay:
    def __init__(self, menu_state: MonsterMenuState) -> None:
        self.menu_state = menu_state
        self.sprite = TextArea(
            font=self.menu_state.font,
            font_color=self.menu_state.font_color,
            rect=Rect(0, 0, 1, 1),
            scaling=self.menu_state.client.context.scaling,
        )
        self.menu_state.sprites.add(self.sprite, layer=LAYER_MONSTER_ICONS)

    def update(self, monster: Monster | None) -> None:
        if not monster:
            self.sprite.image = self.menu_state.shadow_text("")
            return

        stats = OrderedDict(
            [
                (
                    T.translate("short_hp"),
                    f"{monster.current_hp}/{monster.hp}",
                ),
                (T.translate("armour"), str(monster.armour)),
                (T.translate("dodge"), str(monster.dodge)),
                (T.translate("melee"), str(monster.melee)),
                (T.translate("ranged"), str(monster.ranged)),
                (T.translate("speed"), str(monster.speed)),
            ]
        )

        max_len = max(len(label) for label in stats.keys())
        text = "\n".join(
            f"{label:<{max_len}}: {value}" for label, value in stats.items()
        )

        self.sprite.image = self.menu_state.shadow_text(text)
        width, height = self.menu_state.client.context.resolution
        self.sprite.rect.topleft = (width // 10, height // 2 + 50)


class MonsterSpriteDisplay:
    """
    Manages the sprite used to visually represent a monster inside the party menu.

    Each instance tracks a single monster and its corresponding sprite. The class
    is responsible for creating the sprite, positioning it relative to the slot
    rectangle, updating it when the selected monster changes, and removing it
    cleanly from the menu state's sprite group when no longer needed.
    """

    def __init__(self, menu_state: MonsterMenuState) -> None:
        self.menu_state = menu_state
        self.scaling = self.menu_state.client.context.scaling
        self.resolution = self.menu_state.client.context.resolution
        self.sprite: Sprite | None = None
        self.monster: Monster | None = None

    @staticmethod
    def cleanup(displays: list[MonsterSpriteDisplay]) -> None:
        for display in displays:
            display.remove_sprite()
        displays.clear()

    def update(self, monster: Monster | None, rect: Rect) -> None:
        self.monster = monster

        if monster:
            if self.sprite:
                self.menu_state.sprites.remove(self.sprite)

            renderer = MonsterRenderer(monster, scale=2.5, frame_duration=0.25)
            self.sprite = renderer.get_sprite("menu")
            self.menu_state.sprites.add(self.sprite, layer=LAYER_MONSTER_ICONS)

            width = self.resolution[0]
            margin = int(width * 0.005)
            self.sprite.rect.x = width - (self.sprite.rect.width + margin)
            self.sprite.rect.y = rect.y + self.scaling.scale_int(10)

        else:
            self.remove_sprite()

    def remove_sprite(self) -> None:
        if self.sprite is not None:
            self.menu_state.sprites.remove(self.sprite)
            self.sprite = None
        self.monster = None


class MonsterPortraitDisplay:
    def __init__(self, menu_state: MonsterMenuState) -> None:
        self.menu_state = menu_state
        self.scaling = self.menu_state.client.context.scaling
        self.resolution = self.menu_state.client.context.resolution
        self.portrait = Sprite()
        self.portrait.rect = Rect(0, 0, 0, 0)
        self.menu_state.sprites.add(self.portrait, layer=LAYER_PORTRAIT)

    def update(self, monster: Monster | None) -> None:
        image = None
        if monster is not None:
            try:
                scale = self.menu_state.client.context.scale
                renderer = MonsterRenderer(monster, scale=scale)
                sprite = renderer.get_sprite("front")
                image = sprite.image
            except Exception:
                pass

        image = image or Surface((1, 1), SRCALPHA)

        self.portrait.image = image
        width, height = self.resolution
        self.portrait.rect = image.get_rect(
            centerx=width // 4,
            top=height // 12,
        )

    def animate_down(self) -> None:
        ani = self.menu_state.animate(
            self.portrait.rect,
            y=-self.scaling.scale_int(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.schedule(self.animate_up, ScheduleType.ON_FINISH)

    def animate_up(self) -> None:
        ani = self.menu_state.animate(
            self.portrait.rect,
            y=self.scaling.scale_int(5),
            duration=1,
            transition="in_out_quad",
            relative=True,
        )
        ani.schedule(self.animate_down, ScheduleType.ON_FINISH)


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

            window = GraphicBox(
                Rect(0, 0, 3, 3),
                border,
                background=background,
            )
            self.borders[border_type] = window

    def get_border(self, selected: bool, filled: bool) -> GraphicBox:
        if selected:
            return self.borders["active"]
        elif filled:
            return self.borders["filled"]
        else:
            return self.borders["empty"]


class MonsterSlotRenderer:
    """Unified renderer for monster slot layout."""

    def __init__(
        self,
        context: DisplayContext,
        font: Font,
        hp_bar: HpBar,
        font_color: ColorLike,
    ):
        self.context = context
        self.scaling = context.scaling
        self.font = font
        self.hp_bar = hp_bar
        self.font_color = font_color
        self.slot_border = MonsterSlotBorder()

    def render_slot(
        self,
        surface: Surface,
        rect: Rect,
        monster: Monster | None,
        in_focus: bool,
    ) -> None:
        surface.fill(TRANSPARENT_COLOR)

        filled = monster is not None
        border = self.slot_border.get_border(in_focus, filled)
        border.draw(surface)

        if not monster:
            return

        padding = self.scaling.scale_int(6)
        content = rect.inflate(-padding, -padding)

        upper_label = f"{monster.name}{monster.gender_symbol}"

        text_rect = rect.inflate(-padding, -padding)
        draw_text(
            surface,
            upper_label,
            text_rect,
            scaling=self.scaling,
            font=self.font,
        )

        text_rect.top = rect.bottom - self.scaling.scale_int(7)
        bottom_label = f"  Lv {monster.level}"
        draw_text(
            surface,
            bottom_label,
            text_rect,
            scaling=self.scaling,
            font=self.font,
        )

        hp_width = int(content.width * 0.35)
        hp_rect = Rect(0, 0, hp_width, self.scaling.scale_int(8))
        hp_rect.right = content.right
        hp_rect.centery = content.centery

        self.hp_bar.value = monster.hp_ratio
        self.hp_bar.draw(surface, hp_rect)

        self._draw_icons(surface, monster, rect)

    def _draw_icons(
        self,
        surface: Surface,
        monster: Monster,
        content: Rect,
    ) -> None:
        icon_y = content.top + self.scaling.scale_int(4)

        for i, status in enumerate(monster.status.get_statuses()):
            if status.icon:
                img = load_and_scale(status.icon)
                x = int(content.width * 0.45) + i * (
                    img.get_width() + self.scaling.scale_int(4)
                )
                x += content.left
                surface.blit(img, (x, icon_y))

        if monster.held_item:
            item_img = load_and_scale(monster.held_item.sprite, 1.5)
            x = int(content.width * 0.45) + len(
                monster.status.get_statuses()
            ) * (self.scaling.scale_int(4) + item_img.get_width())
            x += content.left
            surface.blit(item_img, (x, icon_y))
