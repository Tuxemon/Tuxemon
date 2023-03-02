# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence, Tuple

import pygame_menu
from pygame_menu import baseimage, locals, widgets

from tuxemon import graphics, prepare
from tuxemon.db import db
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session
from tuxemon.states.journal import MonsterInfoState
from tuxemon.states.monster import MonsterMenuState
from tuxemon.tools import open_choice_dialog, open_dialog

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.animation import Animation
    from tuxemon.monster import Monster


MenuGameObj = Callable[[], object]

HIDDEN = "hidden_kennel"
HIDDEN_LIST = [HIDDEN]


class MonsterTakeState(PygameMenuState):
    """Menu for the Monster Take state.

    Shows all tuxemon currently in a storage kennel, and selecting one puts it
    into your current party."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Monster],
    ) -> None:
        # it regroups kennel operations: pick up, move and release
        def kennel_options(instance_id: str) -> None:

            # retrieves the monster from the iid
            iid = uuid.UUID(instance_id)
            mon = self.player.find_monster_in_storage(iid)

            # list with all the kennels and removes where we are
            kennels = list(local_session.player.monster_boxes.keys())
            kennels.remove(self.box_name)

            # updates the kennel and executes operation
            def update_kennel(mon: Monster, box: str) -> None:
                self.client.pop_state()
                self.client.pop_state()
                if len(kennels) >= 2:
                    self.client.pop_state()
                self.player.remove_monster_from_storage(mon)
                self.player.monster_boxes[box].append(mon)

            # opens choice dialog (move monster)
            def change_kennel(mon: Monster) -> None:
                var_menu = []
                for box in kennels:
                    text = T.translate(box).upper()
                    var_menu.append(
                        (text, text, partial(update_kennel, mon, box))
                    )
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )

            # picks up the monster
            def take_monster(mon: Monster) -> None:
                self.client.pop_state()
                self.client.pop_state()
                self.player.remove_monster_from_storage(mon)
                self.player.add_monster(mon)
                open_dialog(
                    local_session,
                    [
                        T.format(
                            "menu_storage_take_monster", {"name": mon.name}
                        )
                    ],
                )

            # confirms release operation
            def positive(mon: Monster) -> None:
                self.client.pop_state()
                self.client.pop_state()
                self.client.pop_state()
                self.box.remove(mon)
                open_dialog(
                    local_session,
                    [T.format("tuxemon_released", {"name": mon.name})],
                )

            def negative() -> None:
                self.client.pop_state()
                self.client.pop_state()

            # releases the monster
            def release_monster(mon: Monster) -> None:
                var_menu = []
                var_menu.append(("no", T.translate("no").upper(), negative))
                var_menu.append(
                    ("yes", T.translate("yes").upper(), partial(positive, mon))
                )
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )

            # continues kennel_options
            var_menu = []
            # picking up option
            var_menu.append(
                (
                    "pick",
                    T.translate("pick_up").upper(),
                    partial(take_monster, mon),
                )
            )
            # ifs because choice dialog works only with >= 2 elements
            # moving option
            if len(kennels) >= 2:
                var_menu.append(
                    (
                        "move",
                        T.translate("monster_menu_move").upper(),
                        partial(change_kennel, mon),
                    )
                )
            elif len(kennels) == 1:
                msg = T.format(
                    "move_to_kennel",
                    {
                        "box": T.translate(kennels[0]),
                    },
                ).upper()
                var_menu.append(
                    ("move", msg, partial(update_kennel, mon, kennels[0]))
                )
            # releasing option
            var_menu.append(
                (
                    "release",
                    T.translate("monster_menu_release").upper(),
                    partial(release_monster, mon),
                ),
            )
            # creates the choice dialog
            open_choice_dialog(
                local_session,
                menu=(var_menu),
                escape_key_exits=True,
            )

        def description(mon: Monster) -> None:
            self.client.push_state(MonsterInfoState(monster=mon))

        # it prints monsters inside the screen: image + button
        for monster in items:
            label = T.translate(monster.name).upper()
            iid = monster.instance_id.hex
            results = db.lookup(monster.slug, table="monster").dict()
            new_image = pygame_menu.BaseImage(
                graphics.transform_resource_filename(
                    results["sprites"]["menu1"] + ".png"
                ),
                drawing_position=baseimage.POSITION_CENTER,
            )
            new_image.scale(prepare.SCALE, prepare.SCALE)
            menu.add.banner(
                new_image,
                partial(kennel_options, iid),
                selection_effect=widgets.HighlightSelection(),
            )
            menu.add.button(label, partial(description, monster))

        # menu
        menu.set_title(
            T.format(
                "kennel_label",
                {
                    "box": T.translate(self.box_name).upper(),
                    "qty": len(self.box),
                },
            )
        ).center_content()

    def __init__(self, box_name: str) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/bg_pcstate.png"
            ),
            drawing_position=baseimage.POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        # menu
        theme.title = True
        theme.title_background_color = (197, 232, 234)
        theme.title_font_size = round(0.025 * width)
        theme.title_font_color = (10, 10, 10)
        theme.title_close_button = False
        theme.title_bar_style = widgets.MENUBAR_STYLE_ADAPTIVE

        columns = 3

        self.box_name = box_name
        self.player = local_session.player
        self.box = self.player.monster_boxes[self.box_name]

        num_mons = len(self.box)
        # Widgets are like a pygame_menu label, image, etc.
        num_widgets_per_monster = 2
        rows = int(num_mons * num_widgets_per_monster / columns) + 1
        # Make sure rows are divisible by num_widgets
        while rows % num_widgets_per_monster != 0:
            rows += 1

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        menu_items_map = []
        for monster in self.box:
            menu_items_map.append(monster)

        self.add_menu_items(self.menu, menu_items_map)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False


class MonsterBoxChooseState(PygameMenuState):
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
        items: Sequence[Tuple[str, MenuGameObj]],
    ) -> None:

        menu.add.vertical_fill()
        for key, callback in items:
            num_mons = local_session.player.monster_boxes[key]
            label = T.format(
                "kennel_label",
                {
                    "box": T.translate(key).upper(),
                    "qty": len(num_mons),
                },
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

    def get_menu_items_map(self) -> Sequence[Tuple[str, MenuGameObj]]:
        """
        Return a list of menu options and callbacks, to be overridden by
        class descendents.
        """
        return []

    def change_state(self, state: str, **kwargs: Any) -> Callable[[], object]:
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


class MonsterBoxChooseStorageState(MonsterBoxChooseState):
    """Menu to choose a box, which you can then take a tuxemon from."""

    def get_menu_items_map(self) -> Sequence[Tuple[str, MenuGameObj]]:
        player = local_session.player
        menu_items_map = []
        for box_name, monsters in player.monster_boxes.items():
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


class MonsterBoxChooseDropOffState(MonsterBoxChooseState):
    """Menu to choose a box, which you can then drop off a tuxemon into."""

    def get_menu_items_map(self) -> Sequence[Tuple[str, MenuGameObj]]:
        player = local_session.player
        menu_items_map = []
        for box_name, monsters in player.monster_boxes.items():
            if box_name not in HIDDEN_LIST:
                menu_callback = self.change_state(
                    "MonsterDropOffState", box_name=box_name
                )
            menu_items_map.append((box_name, menu_callback))
        return menu_items_map


class MonsterDropOffState(MonsterMenuState):
    """Shows all Tuxemon in player's party, puts it into box if selected."""

    def __init__(self, box_name: str) -> None:
        super().__init__()

        self.box_name = box_name

    def on_menu_selection(
        self,
        menu_item: MenuItem[Optional[Monster]],
    ) -> None:
        player = local_session.player
        monster = menu_item.game_object
        assert monster

        player.monster_boxes[self.box_name].append(monster)
        player.remove_monster(monster)

        self.client.pop_state(self)
