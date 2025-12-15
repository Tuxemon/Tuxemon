# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Optional
from uuid import UUID

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.animation import ScheduleType
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.state.state import State
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.tools import fix_measure, open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.client import LocalPygameClient
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC


MenuGameObj = Callable[[], object]


MAX_BOX = prepare.MAX_KENNEL


class MonsterActionHandler:
    def __init__(
        self,
        client: LocalPygameClient,
        char: NPC,
        box_name: str,
        source_state: str,
    ) -> None:
        self.client = client
        self.char = char
        self.box_name = box_name
        self.source_state = source_state
        self.monster_boxes = char.monster_boxes

    def pick(self, monster: Monster) -> None:
        self._clear_states("ChoiceState", "MonsterTakeState")
        self.monster_boxes.remove_from_box("monster", None, monster)
        self.char.party.insert_monster_to_party(
            monster, len(self.char.monsters)
        )
        open_dialog(
            self.client,
            [T.format("menu_storage_take_monster", {"name": monster.name})],
        )

    def move(self, monster: Monster, box_ids: list[str]) -> None:
        if len(box_ids) == 1:
            self.move_monster(monster, box_ids[0], box_ids)
        else:
            options = []
            for box in box_ids:
                text = T.translate(box).upper()
                action = partial(self.move_monster, monster, box, box_ids)
                options.append(
                    ChoiceOption(key=box, display_text=text, action=action)
                )
            open_choice_dialog(
                self.client, menu=MenuOptions(options), escape_key_exits=True
            )

    def release(self, monster: Monster) -> None:
        options = [
            ChoiceOption(
                key="no",
                display_text=T.translate("no").upper(),
                action=partial(self.output, None),
            ),
            ChoiceOption(
                key="yes",
                display_text=T.translate("yes").upper(),
                action=partial(self.output, monster),
            ),
        ]
        open_choice_dialog(
            self.client, menu=MenuOptions(options), escape_key_exits=True
        )

    def move_monster(
        self, monster: Monster, box: str, box_ids: list[str]
    ) -> None:
        self._clear_states("ChoiceState")
        if len(box_ids) >= 2:
            self._clear_states("MonsterTakeState")
        self.monster_boxes.move_monster(self.box_name, box, monster)

    def output(self, monster: Optional[Monster]) -> None:
        self._clear_states("ChoiceState", "MonsterTakeState")
        if monster is not None:
            self.monster_boxes.remove_from_box(
                "monster", self.box_name, monster
            )
            open_dialog(
                self.client,
                [T.format("tuxemon_released", {"name": monster.name})],
            )

    def info(self, mon: Monster) -> None:
        self._clear_states("ChoiceState")
        self.client.state_manager.push_state(
            "MonsterInfoState",
            kwargs={"monster": mon, "source": self.source_state},
        )

    def tech(self, mon: Monster) -> None:
        self._clear_states("ChoiceState")
        self.client.state_manager.push_state(
            "MonsterMovesState",
            kwargs={"monster": mon, "source": self.source_state},
        )

    def item(self, mon: Monster) -> None:
        self._clear_states("ChoiceState")
        self.client.state_manager.push_state(
            "MonsterItemState",
            kwargs={"monster": mon, "source": self.source_state},
        )

    def description_dialog(self, mon: Monster) -> None:
        _info = T.translate("monster_menu_info").upper()
        _tech = T.translate("monster_menu_tech").upper()
        _item = T.translate("monster_menu_item").upper()
        options = [
            ChoiceOption(
                key="info", display_text=_info, action=partial(self.info, mon)
            ),
            ChoiceOption(
                key="tech", display_text=_tech, action=partial(self.tech, mon)
            ),
            ChoiceOption(
                key="item", display_text=_item, action=partial(self.item, mon)
            ),
        ]
        open_choice_dialog(
            self.client, menu=MenuOptions(options), escape_key_exits=True
        )

    def swap(self, box_monster: Monster, party_monster: Monster) -> None:
        self._clear_states("ChoiceState", "MonsterTakeState")

        swapped_out = self.monster_boxes.swap_with_external_monster_by_iid(
            box_monster.instance_id, party_monster
        )

        if self.char.party.replace_monster(party_monster, swapped_out):
            logger.info(
                f"{party_monster.name} swapped with {swapped_out.name}"
            )
        else:
            logger.warning(f"Failed to swap {swapped_out.name}")

        open_dialog(
            self.client,
            [
                T.format(
                    "menu_storage_swap_monster",
                    {
                        "from": party_monster.name,
                        "to": box_monster.name,
                    },
                )
            ],
        )

    def _clear_states(self, *state_names: str) -> None:
        for name in state_names:
            self.client.state_manager.remove_state_by_name(name)


class MonsterTakeState(PygameMenuState):
    """Menu for the Monster Take state.

    Shows all tuxemon currently in a storage kennel, and selecting one puts it
    into your current party."""

    name: ClassVar[str] = "MonsterTakeState"

    def __init__(
        self,
        box_name: str,
        character: NPC,
        swap_target: Optional[Monster] = None,
    ) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PC_KENNEL)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        columns = 3

        self.box_name = box_name
        self.char = character
        self.monster_boxes = self.char.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)
        self.swap_target = swap_target

        # Widgets are like a pygame_menu label, image, etc.
        num_widgets = 3
        rows = math.ceil(len(self.box) / columns) * num_widgets

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        column_width = fix_measure(self.menu._width, 0.33)
        self.menu._column_max_width = [
            column_width,
            column_width,
            column_width,
        ]

        menu_items_map = []
        for monster in self.box:
            menu_items_map.append(monster)

        self.add_menu_items(self.menu, menu_items_map)
        self.reset_theme()

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Monster],
    ) -> None:
        self.monster_boxes = self.char.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)
        handler = MonsterActionHandler(
            self.client, self.char, self.box_name, self.name
        )

        def kennel_options(instance_id: str) -> None:
            iid = UUID(instance_id)
            mon = self.monster_boxes.get_monsters_by_iid(iid)
            if mon is None:
                logger.error(f"Monster {iid} not found")
                return

            box_ids = [
                key
                for key in self.monster_boxes.monster_boxes
                if not self.monster_boxes.is_box_hidden(key, "monster")
            ]
            kennels = [
                key
                for key in box_ids
                if key != self.box_name
                and self.monster_boxes.get_box_size(key, "monster")
                < prepare.MAX_KENNEL
            ]

            swap_target = self.swap_target
            if swap_target:
                actions = {
                    "swap": lambda: handler.swap(mon, swap_target),
                }
            else:
                actions = {}
                if len(self.char.monsters) < prepare.PARTY_LIMIT:
                    actions["pick"] = lambda: handler.pick(mon)
                if kennels:
                    actions["move"] = lambda: handler.move(mon, kennels)
                actions["release"] = lambda: handler.release(mon)

            options = []
            for action, func in actions.items():
                if action == "move" and len(box_ids) < 2:
                    continue
                translated_action = T.translate(action).upper()
                options.append(
                    ChoiceOption(
                        key=action,
                        display_text=translated_action,
                        action=func,
                    )
                )

            open_choice_dialog(
                self.client,
                menu=MenuOptions(options),
                escape_key_exits=True,
            )

        _sorted = sorted(items, key=lambda x: x.slug)
        for monster in _sorted:
            label = T.translate(monster.name).upper()
            iid = monster.instance_id.hex
            new_image = self._create_image(monster.sprite_handler.front_path)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            menu.add.banner(
                new_image,
                partial(kennel_options, iid),
                selection_effect=HighlightSelection(),
            )
            diff = round((monster.hp_ratio) * 100, 1)
            level = f"Lv.{monster.level}"
            menu.add.progress_bar(
                level,
                default=diff,
                font_size=self.font_type.small,
                align=locals.ALIGN_CENTER,
            )
            menu.add.button(
                label,
                partial(handler.description_dialog, monster),
                font_size=self.font_type.small,
                align=locals.ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )

        box_label = T.translate(self.box_name).upper()
        menu.set_title(
            T.format(f"{box_label}: {len(self.box)}/{MAX_BOX}")
        ).center_content()


class MonsterBoxState(PygameMenuState):
    """Menu to choose a tuxemon box."""

    name: ClassVar[str] = "MonsterBoxState"

    def __init__(self, character: NPC) -> None:
        _, height = prepare.SCREEN_SIZE

        super().__init__(height=height)

        self.animation_offset = 0
        self.char = character

        menu_items_map = self.get_menu_items_map()
        self.add_menu_items(self.menu, menu_items_map)

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[tuple[str, MenuGameObj]],
    ) -> None:
        menu.add.vertical_fill()
        for key, callback in items:
            player = self.char
            num_mons = player.monster_boxes.get_box_size(key, "monster")
            label = T.format(
                f"{T.translate(key).upper()}: {num_mons}/{MAX_BOX}"
            )
            menu.add.button(label, callback)
            menu.add.vertical_fill()

        width, height = prepare.SCREEN_SIZE
        widgets_size = menu.get_size(widget=True)
        b_width, b_height = menu.get_scrollarea().get_border_size()
        menu.resize(
            widgets_size[0],
            height - 2 * b_height,
            position=(width + b_width, b_height, False),
        )

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        """
        Return a list of menu options and callbacks, to be overridden by
        class descendants.
        """
        return []

    def change_state(self, state: str, **kwargs: Any) -> partial[State]:
        return partial(
            self.client.state_manager.replace_state, state, **kwargs
        )

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        """
        Animate the menu sliding in.

        Returns:
            Sliding in animation.

        """

        width = self.menu.get_width(border=True)
        self.animation_offset = 0

        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)

        return ani

    def animate_close(self) -> Animation:
        """
        Animate the menu sliding out.

        Returns:
            Sliding out animation.

        """
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)

        return ani


class MonsterStorageState(MonsterBoxState):
    """Menu to choose a box, which you can then take a tuxemon from."""

    name: ClassVar[str] = "MonsterStorageState"

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        menu_items_map = []
        monster_boxes = self.char.monster_boxes
        for box_name, monsters in monster_boxes.monster_boxes.items():
            metadata = monster_boxes.metadata_manager.get(box_name, "monster")
            if metadata is None or not metadata.is_hidden:
                if not monsters:
                    menu_callback = partial(
                        open_dialog,
                        self.client,
                        [T.translate("menu_storage_empty_kennel")],
                    )
                else:
                    menu_callback = self.change_state(
                        "MonsterTakeState",
                        box_name=box_name,
                        character=self.char,
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOffState(MonsterBoxState):
    """Menu to choose a box, which you can then drop off a tuxemon into."""

    name: ClassVar[str] = "MonsterDropOffState"

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        menu_items_map = []
        monster_boxes = self.char.monster_boxes
        for box_name, monsters in monster_boxes.monster_boxes.items():
            metadata = monster_boxes.metadata_manager.get(box_name, "monster")
            if metadata is None or not metadata.is_hidden:
                if len(monsters) < MAX_BOX:
                    menu_callback = self.change_state(
                        "MonsterDropOff",
                        box_name=box_name,
                        character=self.char,
                    )
                else:
                    menu_callback = partial(
                        open_dialog,
                        self.client,
                        [T.translate("menu_storage_full_kennel")],
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOff(MonsterMenuState):
    """Shows all Tuxemon in player's party, puts it into box if selected."""

    name: ClassVar[str] = "MonsterDropOff"

    def __init__(
        self,
        box_name: str,
        character: NPC,
        on_selection: Optional[Callable[[Monster], None]] = None,
    ) -> None:
        super().__init__(monsters=character.monsters)

        self.box_name = box_name
        self.char = character
        self.on_selection = on_selection

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        alive_monsters = [
            mon for mon in self.char.monsters if not mon.is_fainted
        ]
        if monster is not None:
            return len(alive_monsters) != 1 or monster not in alive_monsters
        return True

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
    ) -> None:
        monster = menu_item.game_object
        assert monster

        if monster.plague.is_infected():
            open_dialog(
                self.client,
                [T.translate("menu_storage_infected_monster")],
            )
            return

        if self.on_selection:
            self.on_selection(monster)
            self.client.state_manager.pop_state(self)
        else:
            self.char.monster_boxes.add_monster(self.box_name, monster)
            self.char.party.remove_monster(monster)
            self.client.state_manager.pop_state(self)
