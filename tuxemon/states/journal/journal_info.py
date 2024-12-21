# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Optional

import pygame_menu
from pygame_menu import locals

from tuxemon import formula, prepare
from tuxemon.db import MonsterModel, SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session

lookup_cache: dict[str, MonsterModel] = {}


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


def _lookup_monsters() -> None:
    monsters = list(db.database["monster"])
    for mon in monsters:
        results = db.lookup(mon, table="monster")
        if results.txmn_id > 0:
            lookup_cache[mon] = results


class JournalInfoState(PygameMenuState):
    """Shows journal (screen 3/3)."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monster: MonsterModel,
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
        types = " ".join(map(lambda s: T.translate(s.name), monster.types))
        # weight and height
        player = local_session.player
        unit = player.game_variables.get("unit_measure", prepare.METRIC)
        if unit == prepare.METRIC:
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
        name = T.translate(monster.slug).upper()
        lab1: Any = menu.add.label(
            title=name,
            label_id="name",
            font_size=self.font_size_big,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fix_measure(width, 0.50), fix_measure(height, 0.15))
        # weight
        _weight = f"{mon_weight} {unit_weight}"
        lab2: Any = menu.add.label(
            title=_weight,
            label_id="weight",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab2.translate(fix_measure(width, 0.50), fix_measure(height, 0.25))
        # height
        _height = f"{mon_height} {unit_height}"
        lab3: Any = menu.add.label(
            title=_height,
            label_id="height",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab3.translate(fix_measure(width, 0.65), fix_measure(height, 0.25))
        # type
        _type = T.translate("monster_menu_type")
        lab4: Any = menu.add.label(
            title=_type,
            label_id="type_label",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab4.translate(fix_measure(width, 0.50), fix_measure(height, 0.30))
        path1 = f"gfx/ui/icons/element/{monster.types[0].name}_type.png"
        type_image_1 = self._create_image(path1)
        if len(monster.types) > 1:
            path2 = f"gfx/ui/icons/element/{monster.types[1].name}_type.png"
            type_image_2 = self._create_image(path2)
            menu.add.image(type_image_1, float=True).translate(
                fix_measure(width, 0.17), fix_measure(height, 0.29)
            )
            menu.add.image(type_image_2, float=True).translate(
                fix_measure(width, 0.19), fix_measure(height, 0.29)
            )
        else:
            menu.add.image(type_image_1, float=True).translate(
                fix_measure(width, 0.17), fix_measure(height, 0.29)
            )
        types = types if self.caught else "-----"
        lab5: Any = menu.add.label(
            title=types,
            label_id="type_loaded",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab5.translate(fix_measure(width, 0.50), fix_measure(height, 0.35))
        # shape
        menu_shape = T.translate("monster_menu_shape")
        _shape = T.translate(monster.shape)
        shape = f"{menu_shape}: {_shape}"
        lab6: Any = menu.add.label(
            title=shape,
            label_id="shape",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab6.translate(fix_measure(width, 0.50), fix_measure(height, 0.40))
        # species
        spec = T.translate(f"cat_{monster.category}")
        spec = spec if self.caught else "-----"
        species = T.translate("monster_menu_species") + ": " + spec
        lab7: Any = menu.add.label(
            title=species,
            label_id="species",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab7.translate(fix_measure(width, 0.50), fix_measure(height, 0.45))
        # txmn_id
        _txmn_id = f"ID: {monster.txmn_id}"
        lab8: Any = menu.add.label(
            title=_txmn_id,
            label_id="txmn_id",
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab8.translate(fix_measure(width, 0.50), fix_measure(height, 0.10))
        # description
        desc = T.translate(f"{monster.slug}_description")
        desc = desc if self.caught else "-----"
        lab9: Any = menu.add.label(
            title=desc,
            label_id="description",
            font_size=self.font_size_small,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab9.translate(fix_measure(width, 0.01), fix_measure(height, 0.56))
        # evolution
        evo = evo if self.caught else "-----"
        lab10: Any = menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=self.font_size_small,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab10.translate(fix_measure(width, 0.01), fix_measure(height, 0.76))

        # evolution monsters
        if self.caught:
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
        _path = f"gfx/sprites/battle/{monster.slug}-front.png"
        _path = _path if self.caught else prepare.MISSING_IMAGE
        new_image = self._create_image(_path)
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_measure(width, 0.20), fix_measure(height, 0.05)
        )

    def __init__(self, **kwargs: Any) -> None:
        if not lookup_cache:
            _lookup_monsters()
        monster: Optional[MonsterModel] = None
        for element in kwargs.values():
            monster = element["monster"]
        if monster is None:
            raise ValueError("No monster")
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_JOURNAL_INFO)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        checks = local_session.player.tuxepedia.get(monster.slug)
        self.caught = True if checks == SeenStatus.caught else False
        self._monster = monster
        self.add_menu_items(self.menu, monster)
        self.reset_theme()

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        client = self.client
        monsters = list(local_session.player.tuxepedia)
        models = list(lookup_cache.values())
        model_dict = {model.slug: model for model in models}
        monster_models = sorted(
            [model_dict[mov] for mov in monsters if mov in model_dict],
            key=lambda x: x.txmn_id,
        )

        if event.button in (buttons.RIGHT, buttons.LEFT) and event.pressed:
            if not monster_models:
                return None

            current_monster_index = monster_models.index(self._monster)
            new_index = (
                (current_monster_index + 1) % len(monster_models)
                if event.button == buttons.RIGHT
                else (current_monster_index - 1) % len(monster_models)
            )
            client.replace_state(
                "JournalInfoState",
                kwargs={"monster": monster_models[new_index]},
            )

        elif (
            event.button in (buttons.BACK, buttons.B, buttons.A)
            and event.pressed
        ):
            client.pop_state()

        return None
