# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from functools import partial
from typing import Any, Callable, Sequence

import pygame_menu
from pygame_menu import baseimage, locals, widgets

from tuxemon import graphics, prepare
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session
from tuxemon.tools import open_choice_dialog, open_dialog

MenuGameObj = Callable[[], object]


def fix_width(screen_x: int, pos_x: float) -> int:
    """it returns the correct width based on percentage"""
    value = round(screen_x * pos_x)
    return value


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class NuPhone(PygameMenuState):
    """Menu for Nu Phone."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        items: Sequence[Item],
    ) -> None:
        self._no_signal = False

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        def no_signal() -> None:
            open_dialog(
                local_session,
                [T.translate("no_signal")],
            )

        def uninstall(itm: Item) -> None:
            count = sum(
                [1 for ele in self.player.items if ele.slug == itm.slug]
            )
            if count > 1:
                self.player.remove_item(itm)
                self.client.replace_state("NuPhone")
            else:
                open_dialog(
                    local_session,
                    [T.translate("uninstall_app")],
                )

        menu._column_max_width = [
            fix_width(menu._width, 0.25),
            fix_width(menu._width, 0.25),
            fix_width(menu._width, 0.25),
            fix_width(menu._width, 0.25),
        ]

        # menu
        network = ["town", "center", "shop"]
        desc = T.translate("nu_phone")
        if local_session.client.map_type in network:
            desc = T.translate("omnichannel_mobile")
        else:
            desc = T.translate("no_signal")
            self._no_signal = True
        menu.set_title(desc).center_content()

        for item in items:
            label = T.translate(item.name).upper()
            change = None
            if item.slug == "app_banking":
                if self._no_signal is True:
                    change = no_signal
                else:
                    change = change_state("NuPhoneBanking")
            elif item.slug == "app_contacts":
                change = change_state("NuPhoneContacts")
            elif item.slug == "app_map":
                change = change_state("NuPhoneMap")
            new_image = pygame_menu.BaseImage(
                graphics.transform_resource_filename(item.sprite),
                drawing_position=baseimage.POSITION_CENTER,
            )
            new_image.scale(prepare.SCALE, prepare.SCALE)
            menu.add.banner(
                new_image,
                change,
                selection_effect=widgets.HighlightSelection(),
            )
            menu.add.button(
                label, action=partial(uninstall, item), font_size=15
            )
            menu.add.label(item.description, font_size=15, wordwrap=True)

    def __init__(self) -> None:
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

        self.player = local_session.player

        menu_items_map = []
        for itm in self.player.items:
            if (
                itm.category == "phone"
                and itm.slug != "nu_phone"
                and itm.slug != "app_tuxepedia"
            ):
                menu_items_map.append(itm)

        # 4 columns, then 3 rows (image + label + description)
        columns = 4
        rows = math.ceil(len(menu_items_map) / columns) * 3

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        self.add_menu_items(self.menu, menu_items_map)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False


class NuPhoneBanking(PygameMenuState):
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:

        if "bank_account" not in self.player.money:
            self.player.money["bank_account"] = 0
        bank = self.player.money["bank_account"]
        money = self.player.money["player"]
        menu.add.label(
            title=T.translate("wallet") + ": " + str(money),
            label_id="wallet",
            font_size=20,
        )
        menu.add.label(
            title=T.translate("bank") + ": " + str(bank),
            label_id="bank",
            font_size=20,
        )

        elements = [
            100,
            200,
            500,
            1000,
            2000,
            5000,
            10000,
            20000,
            50000,
            100000,
        ]

        def choice_deposit() -> None:
            var_menu = []
            for ele in elements:
                if ele <= money:
                    var_menu.append(
                        (str(ele), str(ele), partial(deposit, ele))
                    )
            if var_menu:
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )
            else:
                open_dialog(
                    local_session,
                    [
                        T.format(
                            "no_money_operation",
                            {"operation": T.translate("deposit")},
                        )
                    ],
                )

        def choice_withdraw() -> None:
            var_menu = []
            for ele in elements:
                if ele <= bank:
                    var_menu.append(
                        (str(ele), str(ele), partial(withdraw, ele))
                    )
            if var_menu:
                open_choice_dialog(
                    local_session,
                    menu=(var_menu),
                    escape_key_exits=True,
                )
            else:
                open_dialog(
                    local_session,
                    [
                        T.format(
                            "no_money_operation",
                            {"operation": T.translate("withdraw")},
                        )
                    ],
                )

        def deposit(amount: int) -> None:
            self.client.pop_state()
            self.client.pop_state()
            self.player.money["player"] -= amount
            self.player.money["bank_account"] += amount

        def withdraw(amount: int) -> None:
            self.client.pop_state()
            self.client.pop_state()
            self.player.money["player"] += amount
            self.player.money["bank_account"] -= amount

        menu.add.vertical_margin(100)
        # deposit
        menu.add.button(
            title=T.translate("deposit").upper(),
            action=choice_deposit,
            button_id="deposit",
            font_size=20,
            selection_effect=widgets.HighlightSelection(),
        )
        menu.add.vertical_margin(100)
        # withdraw
        menu.add.button(
            title=T.translate("withdraw").upper(),
            action=choice_withdraw,
            button_id="withdraw",
            font_size=20,
            selection_effect=widgets.HighlightSelection(),
        )
        # menu
        menu.set_title(T.translate("app_banking")).center_content()

    def __init__(self) -> None:
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

        self.player = local_session.player

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False


class NuPhoneContacts(PygameMenuState):
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        def choice(slug: str, phone: str) -> None:
            label = (
                T.translate("action_call") + " " + T.translate(slug).upper()
            )
            var_menu = []
            var_menu.append((label, label, partial(call, phone)))
            open_choice_dialog(
                local_session,
                menu=(var_menu),
                escape_key_exits=True,
            )

        def call(phone: str) -> None:
            self.client.pop_state()
            self.client.pop_state()
            # from spyder_cotton_town.tmx to spyder_cotton_town
            map = self.client.get_map_name()
            map_name = map.split(".")[0]
            # new string map + phone
            new_label = map_name + phone
            if T.translate(new_label) != new_label:
                open_dialog(
                    local_session,
                    [T.translate(new_label)],
                )
            else:
                open_dialog(
                    local_session,
                    [T.translate("phone_no_answer")],
                )

        # slug and phone number from the tuple
        for slug, phone in self.player.contacts.items():
            menu.add.button(
                title=T.translate(slug) + " " + phone,
                action=partial(choice, slug, phone),
                button_id=slug,
                font_size=20,
                selection_effect=widgets.HighlightSelection(),
            )
            menu.add.vertical_margin(25)

        # menu
        menu.set_title(T.translate("app_contacts")).center_content()

    def __init__(self) -> None:
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

        self.player = local_session.player

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False


class NuPhoneMap(PygameMenuState):
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        menu.add.label(
            title=T.translate("leather_town"),
            selectable=True,
            float=True,
            selection_effect=widgets.HighlightSelection(),
            selection_color=(232, 48, 48),
            font_size=20,
            background_color=(232, 48, 48),
        ).translate(
            fix_width(menu._width, 0.20), fix_height(menu._height, -0.03)
        )

        menu.add.label(
            title=T.translate("cotton_town"),
            selectable=True,
            float=True,
            selection_effect=widgets.HighlightSelection(),
            selection_color=(232, 48, 48),
            font_size=20,
            background_color=(232, 48, 48),
        ).translate(
            fix_width(menu._width, 0.20), fix_height(menu._height, 0.08)
        )

        menu.add.label(
            title=T.translate("paper_town"),
            selectable=True,
            float=True,
            selection_effect=widgets.HighlightSelection(),
            selection_color=(232, 48, 48),
            font_size=20,
            background_color=(232, 48, 48),
        ).translate(
            fix_width(menu._width, 0.20), fix_height(menu._height, 0.18)
        )

        menu.add.label(
            title=T.translate("candy_town"),
            selectable=True,
            float=True,
            selection_effect=widgets.HighlightSelection(),
            selection_color=(232, 48, 48),
            font_size=20,
            background_color=(232, 48, 48),
        ).translate(
            fix_width(menu._width, -0.20), fix_height(menu._height, 0.18)
        )

        menu.add.label(
            title=T.translate("timber_town"),
            selectable=True,
            float=True,
            selection_effect=widgets.HighlightSelection(),
            selection_color=(232, 48, 48),
            font_size=20,
            background_color=(232, 48, 48),
        ).translate(
            fix_width(menu._width, -0.20), fix_height(menu._height, -0.03)
        )

        menu.add.label(
            title=T.translate("flower_city"),
            selectable=True,
            float=True,
            selection_effect=widgets.HighlightSelection(),
            selection_color=(232, 48, 48),
            font_size=20,
            background_color=(232, 48, 48),
        ).translate(
            fix_width(menu._width, -0.15), fix_height(menu._height, -0.15)
        )
        # menu
        menu.set_title(title=T.translate("app_map")).center_content()

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/new_spyder_map.png"
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

        self.player = local_session.player

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
        theme.title = False
