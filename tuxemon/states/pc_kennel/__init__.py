# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
import uuid
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.db import PlagueType
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.session import local_session
from tuxemon.state import State
from tuxemon.states.monster import MonsterMenuState
from tuxemon.tools import open_choice_dialog, open_dialog

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.monster import Monster


MenuGameObj = Callable[[], object]


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


HIDDEN = "hidden_kennel"
HIDDEN_LIST = [HIDDEN]
MAX_BOX = prepare.MAX_KENNEL


class MonsterTakeState(PygameMenuState):
    """Menu for the Monster Take state.

    Shows all tuxemon currently in a storage kennel, and selecting one puts it
    into your current party."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Monster],
    ) -> None:
        self.monster_boxes = self.player.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)

        def kennel_options(instance_id: str) -> None:
            iid = uuid.UUID(instance_id)
            mon = self.monster_boxes.get_monsters_by_iid(iid)
            if mon is None:
                logger.error(f"Monster {iid} not found")
                return

            kennels = [
                key
                for key, value in self.monster_boxes.monster_boxes.items()
                if len(value) < MAX_BOX
                and key not in HIDDEN_LIST
                and key != self.box_name
            ]

            box_ids = [
                key
                for key, value in self.monster_boxes.monster_boxes.items()
                if len(value) < MAX_BOX and key not in HIDDEN_LIST
            ]

            actions = {
                "pick": lambda: pick(mon),
                "move": lambda: move(mon, kennels),
                "release": lambda: release(mon),
            }

            menu = []
            for action, func in actions.items():
                if action == "move" and len(box_ids) < 2:
                    continue
                menu.append((action, T.translate(action).upper(), func))

            open_choice_dialog(
                local_session,
                menu=menu,
                escape_key_exits=True,
            )

        def pick(monster: Monster) -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("MonsterTakeState")
            self.monster_boxes.remove_monster(monster)
            self.player.add_monster(monster, len(self.player.monsters))
            open_dialog(
                local_session,
                [
                    T.format(
                        "menu_storage_take_monster", {"name": monster.name}
                    )
                ],
            )

        def move(monster: Monster, box_ids: list[str]) -> None:
            if len(box_ids) == 1:
                move_monster(monster, box_ids[0], box_ids)
            else:
                var_menu = []
                for box in box_ids:
                    text = T.translate(box).upper()
                    var_menu.append(
                        (
                            text,
                            text,
                            partial(move_monster, monster, box, box_ids),
                        )
                    )
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )

        def release(monster: Monster) -> None:
            var_menu = []
            var_menu.append(
                ("no", T.translate("no").upper(), partial(output, None))
            )
            var_menu.append(
                ("yes", T.translate("yes").upper(), partial(output, monster))
            )
            open_choice_dialog(
                local_session,
                menu=(var_menu),
                escape_key_exits=True,
            )

        def move_monster(
            monster: Monster, box: str, box_ids: list[str]
        ) -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("ChoiceState")
            if len(box_ids) >= 2:
                self.client.remove_state_by_name("MonsterTakeState")
            self.monster_boxes.move_monster(self.box_name, box, monster)

        def output(monster: Optional[Monster]) -> None:
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("ChoiceState")
            self.client.remove_state_by_name("MonsterTakeState")
            if monster is not None:
                self.monster_boxes.remove_monster_from(self.box_name, monster)
                open_dialog(
                    local_session,
                    [T.format("tuxemon_released", {"name": monster.name})],
                )

        def description(mon: Monster) -> None:
            params = {"monster": mon, "source": self.name}
            self.client.push_state("MonsterInfoState", kwargs=params)

        # it prints monsters inside the screen: image + button
        _sorted = sorted(items, key=lambda x: x.slug)
        for monster in _sorted:
            label = T.translate(monster.name).upper()
            iid = monster.instance_id.hex
            new_image = self._create_image(monster.front_battle_sprite)
            new_image.scale(prepare.SCALE * 0.5, prepare.SCALE * 0.5)
            menu.add.banner(
                new_image,
                partial(kennel_options, iid),
                selection_effect=HighlightSelection(),
            )
            diff = round((monster.current_hp / monster.hp) * 100, 1)
            level = f"Lv.{monster.level}"
            menu.add.progress_bar(
                level,
                default=diff,
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
            )
            menu.add.button(
                label,
                partial(description, monster),
                font_size=self.font_size_small,
                align=locals.ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )

        # menu
        box_label = T.translate(self.box_name).upper()
        menu.set_title(
            T.format(f"{box_label}: {len(self.box)}/{MAX_BOX}")
        ).center_content()

    def __init__(self, box_name: str) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PC_KENNEL)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        columns = 3

        self.box_name = box_name
        self.player = local_session.player
        self.monster_boxes = self.player.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)

        # Widgets are like a pygame_menu label, image, etc.
        num_widgets = 3
        rows = math.ceil(len(self.box) / columns) * num_widgets

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        self.menu._column_max_width = [
            fix_measure(self.menu._width, 0.33),
            fix_measure(self.menu._width, 0.33),
            fix_measure(self.menu._width, 0.33),
        ]

        menu_items_map = []
        for monster in self.box:
            menu_items_map.append(monster)

        self.add_menu_items(self.menu, menu_items_map)
        self.reset_theme()


class MonsterBoxState(PygameMenuState):
    """Menu to choose a tuxemon box."""

    def __init__(self) -> None:
        _, height = prepare.SCREEN_SIZE

        super().__init__(height=height)

        self.animation_offset = 0

        menu_items_map = self.get_menu_items_map()
        self.add_menu_items(self.menu, menu_items_map)

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[tuple[str, MenuGameObj]],
    ) -> None:
        menu.add.vertical_fill()
        for key, callback in items:
            player = local_session.player
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
        return partial(self.client.replace_state, state, **kwargs)

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
        ani.update_callback = self.update_animation_position

        return ani

    def animate_close(self) -> Animation:
        """
        Animate the menu sliding out.

        Returns:
            Sliding out animation.

        """
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani


class MonsterStorageState(MonsterBoxState):
    """Menu to choose a box, which you can then take a tuxemon from."""

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        player = local_session.player
        menu_items_map = []
        for box_name, monsters in player.monster_boxes.monster_boxes.items():
            if box_name not in HIDDEN_LIST:
                if not monsters:
                    menu_callback = partial(
                        open_dialog,
                        local_session,
                        [T.translate("menu_storage_empty_kennel")],
                    )
                else:
                    menu_callback = self.change_state(
                        "MonsterTakeState", box_name=box_name
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOffState(MonsterBoxState):
    """Menu to choose a box, which you can then drop off a tuxemon into."""

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        player = local_session.player
        menu_items_map = []
        for box_name, monsters in player.monster_boxes.monster_boxes.items():
            if box_name not in HIDDEN_LIST:
                if len(monsters) < MAX_BOX:
                    menu_callback = self.change_state(
                        "MonsterDropOff", box_name=box_name
                    )
                else:
                    menu_callback = partial(
                        open_dialog,
                        local_session,
                        [T.translate("menu_storage_full_kennel")],
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOff(MonsterMenuState):
    """Shows all Tuxemon in player's party, puts it into box if selected."""

    def __init__(self, box_name: str) -> None:
        super().__init__()

        self.box_name = box_name
        self.player = local_session.player

    def is_valid_entry(self, monster: Optional[Monster]) -> bool:
        alive_monsters = [
            mon
            for mon in self.player.monsters
            if not any("faint" in s.slug for s in mon.status)
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
        if PlagueType.infected in monster.plague.values():
            open_dialog(
                local_session,
                [T.translate("menu_storage_infected_monster")],
            )
        else:
            self.player.monster_boxes.add_monster(self.box_name, monster)
            self.player.remove_monster(monster)
            self.client.pop_state(self)
