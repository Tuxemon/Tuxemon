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
from tuxemon.item.filter import ItemFilter
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.quantity import QuantityMenu
from tuxemon.state.state import State
from tuxemon.states.item_menu import ItemMenuState
from tuxemon.tools import fix_measure, open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.client import LocalPygameClient
    from tuxemon.item.item import Item
    from tuxemon.npc import NPC


MenuGameObj = Callable[[], object]


HIDDEN_LOCKER = "hidden_locker"
HIDDEN_LIST_LOCKER = [HIDDEN_LOCKER]


class ItemActionHandler:
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
        self.item_boxes = char.item_boxes

    def take(self, item: Item, quantity: int) -> None:
        self._clear_states("ChoiceState", self.source_state)

        diff = item.quantity - quantity
        retrieve = self.char.bag.find_item(item.slug)

        if diff <= 0:
            self.item_boxes.remove_item(item)
        else:
            item.set_quantity(diff)

        if retrieve:
            retrieve.increase_quantity(quantity)
        else:
            new_item = Item.create(item.slug)
            self.char.bag.add_item(new_item, quantity)

        open_dialog(
            self.client,
            [
                T.format(
                    "menu_storage_take_item",
                    {"name": item.name, "nr": quantity},
                )
            ],
        )

    def move(
        self, item: Item, target_box: str, all_box_ids: list[str]
    ) -> None:
        self._clear_states("ChoiceState")
        if len(all_box_ids) >= 2:
            self._clear_states(self.source_state)
        self.item_boxes.move_item(self.box_name, target_box, item)

    def disband(self, item: Item, quantity: int) -> None:
        self._clear_states("ChoiceState", self.source_state)

        diff = item.quantity - quantity
        if diff <= 0:
            self.item_boxes.remove_item_from(self.box_name, item)
        else:
            item.set_quantity(diff)

        open_dialog(
            self.client,
            [
                T.format(
                    "item_disbanded",
                    {"name": item.name, "nr": quantity},
                )
            ],
        )

    def _clear_states(self, *state_names: str) -> None:
        for name in state_names:
            self.client.state_manager.remove_state_by_name(name)


class ItemTakeState(PygameMenuState):
    """
    Shows all items currently in a storage locker, and selecting one puts it
    into your bag.
    """

    name: ClassVar[str] = "ItemTakeState"

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Item],
    ) -> None:
        self.item_boxes = self.char.item_boxes
        self.box = self.item_boxes.get_items(self.box_name)
        handler = ItemActionHandler(
            self.client, self.char, self.box_name, self.name
        )

        def locker_options(instance_id: str) -> None:
            iid = UUID(instance_id)
            itm = self.item_boxes.get_items_by_iid(iid)
            if itm is None:
                logger.error(f"Item {iid} not found")
                return

            box_ids = [
                key
                for key in self.item_boxes.item_boxes
                if key not in HIDDEN_LIST_LOCKER
            ]
            lockers = [key for key in box_ids if key != self.box_name]

            def take_callback(quantity: int) -> None:
                handler.take(itm, quantity)

            def disband_callback(quantity: int) -> None:
                handler.disband(itm, quantity)

            def change_callback() -> None:
                options = [
                    ChoiceOption(
                        key=box,
                        display_text=T.translate(box).upper(),
                        action=partial(handler.move, itm, box, box_ids),
                    )
                    for box in lockers
                ]
                open_choice_dialog(
                    self.client,
                    menu=MenuOptions(options),
                    escape_key_exits=True,
                )

            def push_quantity_menu(
                callback: Callable[[int], None], max_quantity: int
            ) -> Callable[[], None]:
                def inner() -> None:
                    self.client.state_manager.push_state(
                        QuantityMenu(
                            callback=callback,
                            max_quantity=max_quantity,
                            quantity=1,
                            shrink_to_items=True,
                        )
                    )

                return inner

            actions = {
                "take": push_quantity_menu(take_callback, itm.quantity),
                "change": change_callback,
                "disband": push_quantity_menu(disband_callback, itm.quantity),
            }

            menu_options = []
            for action, func in actions.items():
                if action == "change" and len(box_ids) < 2:
                    continue
                menu_options.append(
                    ChoiceOption(
                        key=action,
                        display_text=T.translate(action).upper(),
                        action=func,
                    )
                )

            open_choice_dialog(
                self.client,
                menu=MenuOptions(menu_options),
                escape_key_exits=True,
            )

        # it prints items inside the screen: image + button
        _sorted = sorted(items, key=lambda x: x.slug)
        sum_total = []
        for itm in _sorted:
            sum_total.append(itm.quantity)
            label = T.translate(itm.name).upper() + " x" + str(itm.quantity)
            iid = itm.instance_id.hex
            new_image = self._create_image(itm.sprite)
            new_image.scale(prepare.SCALE, prepare.SCALE)
            menu.add.banner(
                new_image,
                partial(locker_options, iid),
                selection_effect=HighlightSelection(),
            )
            menu.add.label(
                label,
                selectable=True,
                font_size=self.font_type.small,
                align=locals.ALIGN_CENTER,
                selection_effect=HighlightSelection(),
            )

        # menu
        box_label = T.translate(self.box_name).upper()
        label = f"{box_label} ({len(self.box)} types - {sum(sum_total)} items)"
        menu.set_title(label).center_content()

    def __init__(self, box_name: str, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PC_LOCKER)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True

        columns = 3

        self.box_name = box_name
        self.char = character
        self.box = self.char.item_boxes.get_items(self.box_name)

        # Widgets are like a pygame_menu label, image, etc.
        num_widgets = 2
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
        for item in self.box:
            menu_items_map.append(item)

        self.add_menu_items(self.menu, menu_items_map)
        self.reset_theme()


class ItemBoxState(PygameMenuState):
    """Menu to choose an item box."""

    name: ClassVar[str] = "ItemBoxState"

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
            num_itms = self.char.item_boxes.get_items(key)
            sum_total = []
            for ele in num_itms:
                sum_total.append(ele.quantity)
            box_label = T.translate(key).upper()
            label = f"{box_label} (T{len(num_itms)}-I{sum(sum_total)})"
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
        """Animate the menu sliding in."""

        width = self.menu.get_width(border=True)
        self.animation_offset = 0

        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)

        return ani

    def animate_close(self) -> Animation:
        """Animate the menu sliding out."""
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.schedule(self.update_animation_position, ScheduleType.ON_UPDATE)

        return ani


class ItemStorageState(ItemBoxState):
    """Menu to choose a box, which you can then take an item from."""

    name: ClassVar[str] = "ItemStorageState"

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        item_boxes = self.char.item_boxes
        menu_items_map = []
        for box_name, items in item_boxes.item_boxes.items():
            if box_name not in HIDDEN_LIST_LOCKER:
                if not items:
                    menu_callback = partial(
                        open_dialog,
                        self.client,
                        [T.translate("menu_storage_empty_locker")],
                    )
                else:
                    menu_callback = self.change_state(
                        "ItemTakeState",
                        box_name=box_name,
                        character=self.char,
                    )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class ItemDropOffState(ItemBoxState):
    """Menu to choose a box, which you can then drop off an item into."""

    name: ClassVar[str] = "ItemDropOffState"

    def get_menu_items_map(self) -> Sequence[tuple[str, MenuGameObj]]:
        item_boxes = self.char.item_boxes
        menu_items_map = []
        for box_name, items in item_boxes.item_boxes.items():
            if box_name not in HIDDEN_LIST_LOCKER:
                menu_callback = self.change_state(
                    "ItemDropOff", box_name=box_name, character=self.char
                )
                menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class ItemDropOff(ItemMenuState):
    """Shows all items in player's bag, puts it into box if selected."""

    name: ClassVar[str] = "ItemDropOff"

    def __init__(self, box_name: str, character: NPC) -> None:
        items_filtered = ItemFilter(character.items)
        items_filtered.set_filter_all_visible()
        super().__init__(
            character=character, source=self.name, item_filter=items_filtered
        )

        self.box_name = box_name
        self.char = character

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Item]],
    ) -> None:
        game_object = menu_item.game_object
        assert game_object

        def deposit(itm: Item, quantity: int) -> None:
            self.client.pop_state(self)
            if quantity <= 0:
                return

            item_boxes = self.char.item_boxes
            box = item_boxes.get_items(self.box_name)

            new_item = Item.create(itm.slug)
            new_item.set_quantity(quantity)

            def find_item_in_box(
                slug: str, items: list[Item]
            ) -> Optional[Item]:
                return next((i for i in items if i.slug == slug), None)

            retrieve = find_item_in_box(itm.slug, box) if box else None
            stored = (
                item_boxes.get_items_by_iid(retrieve.instance_id)
                if retrieve
                else None
            )

            if stored:
                stored.increase_quantity(quantity)
            else:
                item_boxes.add_item(self.box_name, new_item)

            self.char.bag.remove_item(itm, quantity)

        self.client.push_state(
            QuantityMenu(
                callback=partial(deposit, game_object),
                max_quantity=game_object.quantity,
                quantity=1,
                shrink_to_items=True,
            )
        )
