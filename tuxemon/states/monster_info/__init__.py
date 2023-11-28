# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import formula, prepare, tools
from tuxemon.db import db
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class MonsterInfoState(PygameMenuState):
    """
    Shows details of the single monster with the journal
    background graphic.
    """

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monster: Monster,
    ) -> None:
        width = menu._width
        height = menu._height
        menu._width = fix_measure(menu._width, 0.97)
        # history
        evo = ""
        if monster.history:
            if len(monster.history) == 1:
                evo = T.translate("yes_evolution")
            else:
                evo = T.translate("yes_evolutions")
        else:
            evo = T.translate("no_evolution")
        # types
        types = " ".join(map(lambda s: T.translate(s.slug), monster.types))
        # weight and height
        results = db.lookup(monster.slug, table="monster")
        diff_weight, diff_height = formula.weight_height_diff(monster, results)
        unit = local_session.player.game_variables["unit_measure"]
        if unit == "Metric":
            mon_weight = monster.weight
            mon_height = monster.height
            unit_weight = "kg"
            unit_height = "cm"
        else:
            mon_weight = formula.convert_lbs(monster.weight)
            mon_height = formula.convert_ft(monster.height)
            unit_weight = "lb"
            unit_height = "ft"
        # name
        menu._auto_centering = False
        lab1 = menu.add.label(
            title=str(monster.txmn_id) + ". " + monster.name.upper(),
            label_id="name",
            font_size=20,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab1, list)
        lab1.translate(fix_measure(width, 0.50), fix_measure(height, 0.10))
        # level + exp
        exp = monster.total_experience
        lab2 = menu.add.label(
            title="Lv. " + str(monster.level) + " - " + str(exp) + "px",
            label_id="level",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab2, list)
        lab2.translate(fix_measure(width, 0.50), fix_measure(height, 0.15))
        # exp next level
        exp_lv = monster.experience_required(1) - monster.total_experience
        lv = monster.level + 1
        lab3 = menu.add.label(
            title=T.format("tuxepedia_exp", {"exp_lv": exp_lv, "lv": lv}),
            label_id="exp",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab3, list)
        lab3.translate(fix_measure(width, 0.50), fix_measure(height, 0.20))
        # weight
        lab4 = menu.add.label(
            title=str(mon_weight)
            + " "
            + unit_weight
            + " ("
            + str(diff_weight)
            + "%)",
            label_id="weight",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab4, list)
        lab4.translate(fix_measure(width, 0.50), fix_measure(height, 0.25))
        # height
        lab5 = menu.add.label(
            title=str(mon_height)
            + " "
            + unit_height
            + " ("
            + str(diff_height)
            + "%)",
            label_id="height",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab5, list)
        lab5.translate(fix_measure(width, 0.50), fix_measure(height, 0.30))
        # type
        lab6 = menu.add.label(
            title=types,
            label_id="type",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab6, list)
        lab6.translate(fix_measure(width, 0.50), fix_measure(height, 0.35))
        # shape
        lab7 = menu.add.label(
            title=T.translate(monster.shape),
            label_id="shape",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab7, list)
        lab7.translate(fix_measure(width, 0.65), fix_measure(height, 0.35))
        # species
        lab8 = menu.add.label(
            title=monster.category,
            label_id="species",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab8, list)
        lab8.translate(fix_measure(width, 0.50), fix_measure(height, 0.40))
        # taste
        tastes = T.translate("tastes") + ": "
        cold = T.translate("taste_" + monster.taste_cold)
        warm = T.translate("taste_" + monster.taste_warm)
        lab9 = menu.add.label(
            title=tastes + cold + ", " + warm,
            label_id="taste",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab9, list)
        lab9.translate(fix_measure(width, 0.50), fix_measure(height, 0.45))
        # capture
        doc = formula.today_ordinal() - monster.capture
        if doc >= 1:
            ref = (
                T.format("tuxepedia_trade", {"doc": doc})
                if monster.traded
                else T.format("tuxepedia_capture", {"doc": doc})
            )
        else:
            ref = (
                T.translate("tuxepedia_trade_today")
                if monster.traded
                else T.translate("tuxepedia_capture_today")
            )
        lab10 = menu.add.label(
            title=ref,
            label_id="capture",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab10, list)
        lab10.translate(fix_measure(width, 0.50), fix_measure(height, 0.50))
        # hp
        lab11 = menu.add.label(
            title=T.translate("short_hp") + ": " + str(monster.hp),
            label_id="hp",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab11, list)
        lab11.translate(fix_measure(width, 0.80), fix_measure(height, 0.15))
        # armour
        lab12 = menu.add.label(
            title=T.translate("short_armour") + ": " + str(monster.armour),
            label_id="armour",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab12, list)
        lab12.translate(fix_measure(width, 0.80), fix_measure(height, 0.20))
        # dodge
        lab13 = menu.add.label(
            title=T.translate("short_dodge") + ": " + str(monster.dodge),
            label_id="dodge",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab13, list)
        lab13.translate(fix_measure(width, 0.80), fix_measure(height, 0.25))
        # melee
        lab14 = menu.add.label(
            title=T.translate("short_melee") + ": " + str(monster.melee),
            label_id="melee",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab14, list)
        lab14.translate(fix_measure(width, 0.80), fix_measure(height, 0.30))
        # ranged
        lab15 = menu.add.label(
            title=T.translate("short_ranged") + ": " + str(monster.ranged),
            label_id="ranged",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab15, list)
        lab15.translate(fix_measure(width, 0.80), fix_measure(height, 0.35))
        # speed
        lab16 = menu.add.label(
            title=T.translate("short_speed") + ": " + str(monster.speed),
            label_id="speed",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab16, list)
        lab16.translate(fix_measure(width, 0.80), fix_measure(height, 0.40))
        # description
        lab17 = menu.add.label(
            title=monster.description,
            label_id="description",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab17, list)
        lab17.translate(fix_measure(width, 0.01), fix_measure(height, 0.56))
        # history
        lab18 = menu.add.label(
            title=evo,
            label_id="history",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab18, list)
        lab18.translate(fix_measure(width, 0.01), fix_measure(height, 0.76))

        # history monsters
        f = menu.add.frame_h(
            float=True,
            width=fix_measure(width, 0.95),
            height=fix_measure(width, 0.05),
            frame_id="histories",
        )
        f.translate(fix_measure(width, 0.02), fix_measure(height, 0.80))
        f._relax = True
        elements = []
        for ele in monster.history:
            elements.append(ele.mon_slug)
        labels = [
            menu.add.label(
                title=f"{T.translate(ele).upper()}",
                align=locals.ALIGN_LEFT,
                font_size=15,
            )
            for ele in elements
        ]
        for elements in labels:
            f.pack(elements)
        # image
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(monster.front_battle_sprite),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_measure(width, 0.20), fix_measure(height, 0.05)
        )
        # tuxeball
        tuxeball = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                f"gfx/items/{monster.capture_device}.png"
            ),
        )
        capture_device = menu.add.image(image_path=tuxeball)
        capture_device.set_float(origin_position=True)
        capture_device.translate(
            fix_measure(width, 0.50), fix_measure(height, 0.445)
        )

    def __init__(
        self, monster: Monster, source: str = "MonsterMenuState"
    ) -> None:
        self._monster = monster
        self._source = source
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/tux_info.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu, monster)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if (
            self._source == "WorldMenuState"
            or self._source == "MonsterMenuState"
        ):
            monsters = local_session.player.monsters
            nr_monsters = len(monsters)
            slot = monsters.index(self._monster)
            if event.button == buttons.RIGHT and event.pressed:
                if slot < (nr_monsters - 1):
                    slot += 1
                    self.client.replace_state(
                        MonsterInfoState(monster=monsters[slot])
                    )
                else:
                    self.client.replace_state(
                        MonsterInfoState(monster=monsters[0])
                    )
            elif event.button == buttons.LEFT and event.pressed:
                if slot > 0:
                    slot -= 1
                    self.client.replace_state(
                        MonsterInfoState(monster=monsters[slot])
                    )
                else:
                    self.client.replace_state(
                        MonsterInfoState(monster=monsters[nr_monsters - 1])
                    )
        if (
            event.button == buttons.BACK
            or event.button == buttons.B
            or event.button == buttons.A
        ) and event.pressed:
            self.client.pop_state()
        return None
