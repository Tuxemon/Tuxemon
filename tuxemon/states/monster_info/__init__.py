# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from typing import Any, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import formula, prepare, tools
from tuxemon.db import db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session


def find_box_name(instance_id: uuid.UUID) -> Optional[str]:
    """
    Finds a monster in the npc's storage boxes and return the box name.

    Parameters:
        instance_id: The instance_id of the monster.

    Returns:
        Box name, or None.

    """
    for box, monsters in local_session.player.monster_boxes.items():
        monster = next(
            (m for m in monsters if m.instance_id == instance_id), None
        )
        if monster is not None:
            return box
    return None


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
        diff_weight = formula.diff_percentage(monster.weight, results.weight)
        diff_height = formula.diff_percentage(monster.height, results.height)
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
        lab1: Any = menu.add.label(
            title=str(monster.txmn_id) + ". " + monster.name.upper(),
            label_id="name",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fix_measure(width, 0.50), fix_measure(height, 0.10))
        # level + exp
        exp = monster.total_experience
        lab2: Any = menu.add.label(
            title="Lv. " + str(monster.level) + " - " + str(exp) + "px",
            label_id="level",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fix_measure(width, 0.50), fix_measure(height, 0.15))
        # exp next level
        exp_lv = monster.experience_required(1) - monster.total_experience
        lv = monster.level + 1
        lab3: Any = menu.add.label(
            title=T.format("tuxepedia_exp", {"exp_lv": exp_lv, "lv": lv}),
            label_id="exp",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fix_measure(width, 0.50), fix_measure(height, 0.20))
        # weight
        lab4: Any = menu.add.label(
            title=str(mon_weight)
            + " "
            + unit_weight
            + " ("
            + str(diff_weight)
            + "%)",
            label_id="weight",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fix_measure(width, 0.50), fix_measure(height, 0.25))
        # height
        lab5: Any = menu.add.label(
            title=str(mon_height)
            + " "
            + unit_height
            + " ("
            + str(diff_height)
            + "%)",
            label_id="height",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab5.translate(fix_measure(width, 0.50), fix_measure(height, 0.30))
        # type
        lab6: Any = menu.add.label(
            title=types,
            label_id="type",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab6.translate(fix_measure(width, 0.50), fix_measure(height, 0.35))
        # shape
        lab7: Any = menu.add.label(
            title=T.translate(monster.shape),
            label_id="shape",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab7.translate(fix_measure(width, 0.65), fix_measure(height, 0.35))
        # species
        lab8: Any = menu.add.label(
            title=monster.category,
            label_id="species",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab8.translate(fix_measure(width, 0.50), fix_measure(height, 0.40))
        # taste
        tastes = T.translate("tastes") + ": "
        cold = T.translate("taste_" + monster.taste_cold)
        warm = T.translate("taste_" + monster.taste_warm)
        lab9: Any = menu.add.label(
            title=tastes + cold + ", " + warm,
            label_id="taste",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
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
        lab10: Any = menu.add.label(
            title=ref,
            label_id="capture",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab10.translate(fix_measure(width, 0.50), fix_measure(height, 0.50))
        # hp
        lab11: Any = menu.add.label(
            title=T.translate("short_hp") + ": " + str(monster.hp),
            label_id="hp",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab11.translate(fix_measure(width, 0.80), fix_measure(height, 0.15))
        # armour
        lab12: Any = menu.add.label(
            title=T.translate("short_armour") + ": " + str(monster.armour),
            label_id="armour",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab12.translate(fix_measure(width, 0.80), fix_measure(height, 0.20))
        # dodge
        lab13: Any = menu.add.label(
            title=T.translate("short_dodge") + ": " + str(monster.dodge),
            label_id="dodge",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab13.translate(fix_measure(width, 0.80), fix_measure(height, 0.25))
        # melee
        lab14: Any = menu.add.label(
            title=T.translate("short_melee") + ": " + str(monster.melee),
            label_id="melee",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab14.translate(fix_measure(width, 0.80), fix_measure(height, 0.30))
        # ranged
        lab15: Any = menu.add.label(
            title=T.translate("short_ranged") + ": " + str(monster.ranged),
            label_id="ranged",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab15.translate(fix_measure(width, 0.80), fix_measure(height, 0.35))
        # speed
        lab16: Any = menu.add.label(
            title=T.translate("short_speed") + ": " + str(monster.speed),
            label_id="speed",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab16.translate(fix_measure(width, 0.80), fix_measure(height, 0.40))
        # description
        lab17: Any = menu.add.label(
            title=monster.description,
            label_id="description",
            font_size=self.font_size_small,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab17.translate(fix_measure(width, 0.01), fix_measure(height, 0.56))
        # history
        lab18: Any = menu.add.label(
            title=evo,
            label_id="history",
            font_size=self.font_size_small,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
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
                font_size=self.font_size_smaller,
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

    def __init__(self, **kwargs: Any) -> None:
        monster: Optional[Monster] = None
        source = ""
        for element in kwargs.values():
            monster = element["monster"]
            source = element["source"]
        if monster is None:
            raise ValueError("No monster")
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                prepare.BG_MONSTER_INFO
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)
        self._source = source
        self._monster = monster
        self.add_menu_items(self.menu, monster)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = self.background_color
        theme.widget_alignment = locals.ALIGN_LEFT

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        param: dict[str, Any] = {}
        param["source"] = self._source
        client = self.client
        if (
            self._source == "WorldMenuState"
            or self._source == "MonsterMenuState"
            or self._source == "MonsterTakeState"
        ):
            if self._source == "MonsterTakeState":
                box = find_box_name(self._monster.instance_id)
                if box is None:
                    raise ValueError("Box doesn't exist")
                monsters = local_session.player.monster_boxes[box]
                nr_monsters = len(monsters)
                slot = monsters.index(self._monster)
            else:
                monsters = local_session.player.monsters
                nr_monsters = len(monsters)
                slot = monsters.index(self._monster)
            if event.button == buttons.RIGHT and event.pressed:
                if slot < (nr_monsters - 1):
                    slot += 1
                    param["monster"] = monsters[slot]
                else:
                    param["monster"] = monsters[0]
                client.replace_state("MonsterInfoState", kwargs=param)
            elif event.button == buttons.LEFT and event.pressed:
                if slot > 0:
                    slot -= 1
                    param["monster"] = monsters[slot]
                else:
                    param["monster"] = monsters[nr_monsters - 1]
                client.replace_state("MonsterInfoState", kwargs=param)
        if (
            event.button == buttons.BACK
            or event.button == buttons.B
            or event.button == buttons.A
        ) and event.pressed:
            client.pop_state()
        return None
