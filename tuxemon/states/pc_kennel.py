# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import UUID

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.graphics import scale_surface
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.transitions import SlideRight
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.platform.const.graphics import BG_PC_KENNEL
from tuxemon.platform.const.sizes import MAX_KENNEL, PARTY_LIMIT
from tuxemon.state.state import State
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.tools import fix_measure, open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import (
    MenuOptions,
    create_choice_options,
    create_yes_no_options,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster


MenuGameObj = Callable[[], object]


MAX_BOX = MAX_KENNEL


class MonsterActionHandler:
    def __init__(
        self,
        client: BaseClient,
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
        self.char.party.transfer_monster_to_party(monster)
        open_dialog(
            self.client,
            [T.format("menu_storage_take_monster", {"name": monster.name})],
            dialog_speed="max",
        )

    def move(self, monster: Monster, box_ids: list[str]) -> None:
        if len(box_ids) == 1:
            self.move_monster(monster, box_ids[0], box_ids)
        else:
            actions = {
                box: partial(self.move_monster, monster, box, box_ids)
                for box in box_ids
            }
            options = create_choice_options(actions)
            open_choice_dialog(
                self.client,
                menu=MenuOptions(options),
                escape_key_exits=True,
            )

    def release(self, monster: Monster) -> None:
        options = create_yes_no_options(
            yes_action=partial(self.output, monster),
            no_action=partial(self.output, None),
        )

        open_choice_dialog(
            self.client,
            menu=MenuOptions(options),
            escape_key_exits=True,
        )

    def move_monster(
        self, monster: Monster, box: str, box_ids: list[str]
    ) -> None:
        self._clear_states("ChoiceState")
        if len(box_ids) >= 2:
            self._clear_states("MonsterTakeState")
        self.monster_boxes.move_monster(self.box_name, box, monster)

    def output(self, monster: Monster | None) -> None:
        self._clear_states("ChoiceState", "MonsterTakeState")
        if monster is not None:
            self.monster_boxes.remove_from_box(
                "monster", self.box_name, monster
            )
            open_dialog(
                self.client,
                [T.format("tuxemon_released", {"name": monster.name})],
                dialog_speed="max",
            )

    def info(self, mon: Monster) -> None:
        self._clear_states("ChoiceState")
        self.client.state_manager.push_state(
            "MonsterInfoState",
            **{
                "monster": mon,
                "source": self.source_state,
                "monsters": self.monster_boxes.get_monsters(self.box_name),
            },
        )

    def tech(self, mon: Monster) -> None:
        self._clear_states("ChoiceState")
        self.client.state_manager.push_state(
            "MonsterMovesState",
            **{
                "monster": mon,
                "source": self.source_state,
                "monsters": self.monster_boxes.get_monsters(self.box_name),
            },
        )

    def description_dialog(self, mon: Monster) -> None:
        actions = {
            "info": partial(self.info, mon),
            "tech": partial(self.tech, mon),
        }

        options = create_choice_options(actions)

        open_choice_dialog(
            self.client,
            menu=MenuOptions(options),
            escape_key_exits=True,
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
            dialog_speed="max",
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
        client: BaseClient,
        box_name: str,
        character: NPC,
        swap_target: Monster | None = None,
        **kwargs: Any,
    ) -> None:
        self.box_name = box_name
        self.char = character
        self.monster_boxes = self.char.monster_boxes
        self.box = self.monster_boxes.get_monsters(self.box_name)
        self.swap_target = swap_target

        width, height = client.context.resolution

        columns = 3
        num_widgets = 3
        rows = math.ceil(len(self.box) / columns) * num_widgets

        super().__init__(
            client=client,
            height=height,
            width=width,
            columns=columns,
            rows=rows,
            **kwargs,
        )

        theme = self._setup_theme(BG_PC_KENNEL)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

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

    def kennel_options(
        self, instance_id: str, handler: MonsterActionHandler
    ) -> None:
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
            and self.monster_boxes.get_box_size(key, "monster") < MAX_KENNEL
        ]

        swap_target = self.swap_target
        if swap_target:
            actions = {"swap": lambda: handler.swap(mon, swap_target)}
        else:
            actions = {}
            if len(self.char.monsters) < PARTY_LIMIT:
                actions["pick"] = lambda: handler.pick(mon)
            if kennels:
                actions["move"] = lambda: handler.move(mon, kennels)
            actions["release"] = lambda: handler.release(mon)

        filtered_actions = {
            action: func
            for action, func in actions.items()
            if not (action == "move" and len(box_ids) < 2)
        }

        options = create_choice_options(filtered_actions)
        open_choice_dialog(
            self.client,
            menu=MenuOptions(options),
            escape_key_exits=True,
        )

    def add_menu_items(self, menu: Menu, items: Sequence[Monster]) -> None:
        handler = MonsterActionHandler(
            self.client, self.char, self.box_name, self.name
        )

        _sorted = sorted(items, key=lambda x: x.slug)
        for monster in _sorted:
            label = T.translate(monster.name).upper()
            iid = monster.instance_id.hex
            renderer = MonsterRenderer(monster, scale=self.factor)
            surface = renderer.get_sprite("front").image
            scaled = scale_surface(surface, self.factor * 0.125)
            new_image = self._create_image_from_surface(scaled)
            menu.add.banner(
                new_image,
                partial(self.kennel_options, iid, handler),
                selection_effect=HighlightSelection(),
            )
            diff = round((monster.hp_ratio) * 100, 1)
            level = f"Lv.{monster.level}"
            menu.add.progress_bar(
                level,
                default=diff,
                font_size=self.font_type.small,
                align=ALIGN_CENTER,
            )
            menu.add.button(
                label,
                partial(handler.description_dialog, monster),
                font_size=self.font_type.small,
                align=ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )

        box_label = T.translate(self.box_name).upper()
        menu.set_title(
            T.format(f"{box_label}: {len(self.box)}/{MAX_BOX}")
        ).center_content()


class MonsterBoxState(PygameMenuState):
    """Menu to choose a tuxemon box."""

    name: ClassVar[str] = "MonsterBoxState"

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        width, height = client.context.resolution

        super().__init__(
            client=client, height=height, transition=SlideRight(), **kwargs
        )

        self.char = character

        menu_items_map = self.get_menu_items_map()
        self.add_menu_items(self.menu, menu_items_map)

    def add_menu_items(
        self,
        menu: Menu,
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

        width, height = self.client.context.resolution
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


class MonsterStorageState(MonsterBoxState):
    """Menu to choose a box, which you can then take a tuxemon from."""

    name: ClassVar[str] = "MonsterStorageState"

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        menu_items_map = []
        monster_boxes = self.char.monster_boxes
        for box_name, monsters in monster_boxes.monster_boxes.items():
            if not monster_boxes.is_box_hidden(box_name, "monster"):
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

    def __init__(self, client: BaseClient, *args: Any, **kwargs: Any):
        super().__init__(client, *args, **kwargs)

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        menu_items_map = []
        monster_boxes = self.char.monster_boxes
        for box_name, monsters in monster_boxes.monster_boxes.items():
            if not monster_boxes.is_box_hidden(box_name, "monster"):
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
        client: BaseClient,
        box_name: str,
        character: NPC,
        on_selection: Callable[[Monster], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(client=client, monsters=character.monsters, **kwargs)

        self.box_name = box_name
        self.char = character
        self.on_selection = on_selection

    def is_valid_entry(self, monster: Monster | None) -> bool:
        alive_monsters = [
            mon for mon in self.char.monsters if not mon.is_fainted
        ]
        if monster is not None:
            return len(alive_monsters) != 1 or monster not in alive_monsters
        return True

    def on_menu_selection(
        self,
        menu_item: MenuItem[Monster | None],
    ) -> None:
        monster = menu_item.game_object
        assert monster

        if monster.plague.is_infected():
            open_dialog(
                self.client,
                [T.translate("menu_storage_infected_monster")],
                dialog_speed="max",
            )
            return

        if self.on_selection:
            self.on_selection(monster)
            self.client.state_manager.pop_state(self)
        else:
            self.char.party.transfer_monster_to_box(monster, self.box_name)
            self.client.state_manager.pop_state(self)
