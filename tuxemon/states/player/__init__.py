# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from datetime import date, datetime
from typing import Callable, List

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import formula, prepare, tools
from tuxemon.db import OutputBattle, SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

MenuGameObj = Callable[[], object]


def fix_width(screen_x: int, pos_x: float) -> int:
    """it returns the correct width based on percentage"""
    value = round(screen_x * pos_x)
    return value


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class PlayerState(PygameMenuState):
    """Menu for the Journal Info state.

    Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        width = menu._width
        height = menu._height

        player = local_session.player

        if player.name == "":
            name = T.translate(player.slug).upper()
        else:
            name = player.name.upper()

        # tuxepedia data
        monsters = list(db.database["monster"])
        filters = []
        for mon in monsters:
            results = db.lookup(mon, table="monster")
            if results.txmn_id > 0:
                filters.append(results)
        tuxepedia = list(player.tuxepedia.values())
        caught = tuxepedia.count(SeenStatus.caught)
        seen = tuxepedia.count(SeenStatus.seen) + caught
        percentage = round((seen / len(filters)) * 100, 1)

        msg_progress = T.format(
            "tuxepedia_progress", {"value": str(percentage)}
        )
        msg_seen = T.format(
            "tuxepedia_data_seen",
            {"param": str(seen), "all": str(len(filters))},
        )
        msg_caught = T.format(
            "tuxepedia_data_caught",
            {"param": str(caught), "all": str(len(filters))},
        )
        date_begin = formula.today_ordinal() - int(
            player.game_variables["date_start_game"]
        )
        msg_begin = T.format(
            "player_start_adventure",
            {"date": str(date_begin)},
        )
        tot = len(player.battles)
        won = sum(
            1
            for battle in player.battles
            if battle.outcome == OutputBattle.won
        )
        draw = sum(
            1
            for battle in player.battles
            if battle.outcome == OutputBattle.draw
        )
        lost = sum(
            1
            for battle in player.battles
            if battle.outcome == OutputBattle.lost
        )
        msg_battles = T.format(
            "player_battles",
            {
                "tot": str(tot),
                "won": str(won),
                "draw": str(draw),
                "lost": str(lost),
            },
        )
        # steps
        steps = player.game_variables["steps"]
        if prepare.CONFIG.unit == "metric":
            walked = formula.convert_km(steps)
            unit_walked = "km"
        else:
            walked = formula.convert_mi(steps)
            unit_walked = "mi"
        msg_walked = T.format(
            "player_walked",
            {
                "distance": str(walked),
                "unit": unit_walked,
            },
        )
        # name
        menu._auto_centering = False
        lab1 = menu.add.label(
            title=name,
            label_id="name",
            font_size=30,
            align=locals.ALIGN_LEFT,
            underline=True,
            float=True,
        )
        assert not isinstance(lab1, List)
        lab1.translate(fix_width(width, 0.45), fix_height(height, 0.15))

        # birthday
        def random_dob() -> None:
            self.client.pop_state()
            player.dob = random.randint(0, 365)

        def pseudo_date(name: str) -> None:
            dates: List[str] = []
            if name.find("-"):
                dates = name.split("-")
            else:
                raise ValueError(f"Incorrect format day-month (eg. 3-1)")
            month: int = int(dates[0])
            day: int = int(dates[1]) - 1
            day_of_year = date(2020, month, day).timetuple().tm_yday
            player.dob = day_of_year

        def normal_dob() -> None:
            self.client.pop_state()
            self.client.push_state(
                InputMenu(
                    prompt=T.translate("player_birthday_extended"),
                    callback=pseudo_date,
                    escape_key_exits=False,
                    numerical=True,
                    char_limit=5,
                )
            )

        def set_dob() -> None:
            self.client.pop_state()
            var_menu = []
            var_menu.append(
                ("random", T.translate("random").upper(), random_dob)
            )
            var_menu.append(
                ("normal", T.translate("normal").upper(), normal_dob)
            )
            tools.open_choice_dialog(
                local_session,
                menu=(var_menu),
                escape_key_exits=True,
            )

        if player.dob == 0:
            gen1 = menu.add.button(
                title=T.translate("set_birthday"),
                action=set_dob,
                button_id="generate",
                font_size=15,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            gen1.translate(fix_width(width, 0.45), fix_height(height, 0.25))
        else:
            day_num = str(player.dob)
            day_num.rjust(3 + len(day_num), "0")
            res = datetime.strptime(day_num, "%j").strftime("%m-%d")
            lab2 = menu.add.label(
                title=T.translate("player_birthday") + ": " + str(res),
                label_id="dob",
                font_size=15,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            assert not isinstance(lab2, List)
            lab2.translate(fix_width(width, 0.45), fix_height(height, 0.25))
        # money
        money = player.money["player"]
        lab2 = menu.add.label(
            title=T.translate("wallet") + ": " + str(money),
            label_id="money",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab2, List)
        lab2.translate(fix_width(width, 0.45), fix_height(height, 0.30))
        # seen
        lab3 = menu.add.label(
            title=msg_seen,
            label_id="seen",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab3, List)
        lab3.translate(fix_width(width, 0.45), fix_height(height, 0.35))
        # caught
        lab4 = menu.add.label(
            title=msg_caught,
            label_id="caught",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab4, List)
        lab4.translate(fix_width(width, 0.45), fix_height(height, 0.40))
        # begin adventure
        lab5 = menu.add.label(
            title=msg_begin,
            label_id="begin",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab5, List)
        lab5.translate(fix_width(width, 0.45), fix_height(height, 0.45))
        # walked
        lab6 = menu.add.label(
            title=msg_walked,
            label_id="walked",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab6, List)
        lab6.translate(fix_width(width, 0.45), fix_height(height, 0.50))
        # battles
        lab7 = menu.add.label(
            title=msg_battles,
            label_id="battle",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab7, List)
        lab7.translate(fix_width(width, 0.45), fix_height(height, 0.55))
        # % tuxepedia
        lab8 = menu.add.label(
            title=msg_progress,
            label_id="progress",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab8, List)
        lab8.translate(fix_width(width, 0.45), fix_height(height, 0.10))
        # image
        combat_front = ""
        for ele in player.template:
            combat_front = ele.combat_front
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                "gfx/sprites/player/" + combat_front + ".png"
            ),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_width(width, 0.17), fix_height(height, 0.08)
        )

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/player_info.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
