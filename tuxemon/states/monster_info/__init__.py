# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import formula, prepare
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.time_handler import today_ordinal

lookup_cache: dict[str, MonsterModel] = {}


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results


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
        # evolutions
        evo = T.translate("no_evolution")
        if monster.evolutions:
            evo = T.translate(
                "yes_evolution"
                if len(monster.evolutions) == 1
                else "yes_evolutions"
            )
        # types
        types = " ".join(map(lambda s: T.translate(s.slug), monster.types))
        # weight and height
        models = list(lookup_cache.values())
        results = next(
            (model for model in models if model.slug == monster.slug), None
        )
        if results is None:
            return
        diff_weight = formula.diff_percentage(monster.weight, results.weight)
        diff_height = formula.diff_percentage(monster.height, results.height)
        unit = self.client.config.unit_measure
        if unit == "metric":
            mon_weight = monster.weight
            mon_height = monster.height
            unit_weight = prepare.U_KG
            unit_height = prepare.U_CM
        else:
            mon_weight = formula.convert_lbs(monster.weight)
            mon_height = formula.convert_ft(monster.height)
            unit_weight = prepare.U_LB
            unit_height = prepare.U_FT
        # name
        menu._auto_centering = False
        lab1: Any = menu.add.label(
            title=f"{monster.txmn_id}. {monster.name.upper()}",
            label_id="name",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fix_measure(width, 0.50), fix_measure(height, 0.10))
        # level + exp
        exp = monster.total_experience
        lab2: Any = menu.add.label(
            title=f"Lv. {monster.level} - {exp}px",
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
            title=f"{mon_weight} {unit_weight} ({diff_weight}%)",
            label_id="weight",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fix_measure(width, 0.50), fix_measure(height, 0.25))
        # height
        lab5: Any = menu.add.label(
            title=f"{mon_height} {unit_height} ({diff_height}%)",
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
        tastes = T.translate("tastes")
        cold = T.translate(f"taste_{monster.taste_cold.lower()}")
        warm = T.translate(f"taste_{monster.taste_warm.lower()}")
        lab9: Any = menu.add.label(
            title=f"{tastes}: {cold}, {warm}",
            label_id="taste",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab9.translate(fix_measure(width, 0.50), fix_measure(height, 0.45))
        # capture
        doc = today_ordinal() - monster.capture
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
            title=f"{T.translate('short_hp')}: {monster.hp}",
            label_id="hp",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab11.translate(fix_measure(width, 0.80), fix_measure(height, 0.15))
        # armour
        lab12: Any = menu.add.label(
            title=f"{T.translate('short_armour')}: {monster.armour}",
            label_id="armour",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab12.translate(fix_measure(width, 0.80), fix_measure(height, 0.20))
        # dodge
        lab13: Any = menu.add.label(
            title=f"{T.translate('short_dodge')}: {monster.dodge}",
            label_id="dodge",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab13.translate(fix_measure(width, 0.80), fix_measure(height, 0.25))
        # melee
        lab14: Any = menu.add.label(
            title=f"{T.translate('short_melee')}: {monster.melee}",
            label_id="melee",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab14.translate(fix_measure(width, 0.80), fix_measure(height, 0.30))
        # ranged
        lab15: Any = menu.add.label(
            title=f"{T.translate('short_ranged')}: {monster.ranged}",
            label_id="ranged",
            font_size=self.font_size_smaller,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab15.translate(fix_measure(width, 0.80), fix_measure(height, 0.35))
        # speed
        lab16: Any = menu.add.label(
            title=f"{T.translate('short_speed')}: {monster.speed}",
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
        # evolution
        lab18: Any = menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=self.font_size_small,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab18.translate(fix_measure(width, 0.01), fix_measure(height, 0.76))

        # evolution monsters
        f = menu.add.frame_h(
            float=True,
            width=fix_measure(width, 0.95),
            height=fix_measure(width, 0.05),
            frame_id="histories",
        )
        f.translate(fix_measure(width, 0.02), fix_measure(height, 0.80))
        f._relax = True
        slugs = [ele.monster_slug for ele in monster.evolutions]
        elements = list(dict.fromkeys(slugs))
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
        new_image = self._create_image(monster.front_battle_sprite)
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_measure(width, 0.20), fix_measure(height, 0.05)
        )
        # tuxeball
        tuxeball = self._create_image(
            f"gfx/items/{monster.capture_device}.png"
        )
        capture_device = menu.add.image(image_path=tuxeball)
        capture_device.set_float(origin_position=True)
        capture_device.translate(
            fix_measure(width, 0.50), fix_measure(height, 0.445)
        )

    def __init__(self, **kwargs: Any) -> None:
        if not lookup_cache:
            _lookup_monsters()
        monster: Optional[Monster] = None
        source = ""
        for element in kwargs.values():
            monster = element["monster"]
            source = element["source"]
        if monster is None:
            raise ValueError("No monster")
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_MONSTER_INFO)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)
        self._source = source
        self._monster = monster
        self.add_menu_items(self.menu, monster)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        param: dict[str, Any] = {"source": self._source}
        client = self.client

        if self._source in [
            "WorldMenuState",
            "MonsterMenuState",
            "MonsterTakeState",
        ]:
            monsters = self._get_monsters()
            slot = monsters.index(self._monster)

            if event.button == buttons.RIGHT and event.pressed:
                slot = (slot + 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterInfoState", kwargs=param)
            elif event.button == buttons.LEFT and event.pressed:
                slot = (slot - 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterInfoState", kwargs=param)

        if (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            client.pop_state()

        return None

    def _get_monsters(self) -> list[Monster]:
        if self._source == "MonsterTakeState":
            box = local_session.player.monster_boxes.get_box_name(
                self._monster.instance_id
            )
            if box is None:
                raise ValueError("Box doesn't exist")
            return local_session.player.monster_boxes.get_monsters(box)
        else:
            return local_session.player.monsters
