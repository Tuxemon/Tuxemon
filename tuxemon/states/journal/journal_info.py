# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import formula, prepare, tools
from tuxemon.db import MonsterModel, SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


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
        type_image_1 = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                f"gfx/ui/icons/element/{monster.types[0].name}_type.png"
            ),
        )
        if len(monster.types) > 1:
            path = f"gfx/ui/icons/element/{monster.types[1].name}_type.png"
            type_image_2 = pygame_menu.BaseImage(
                tools.transform_resource_filename(path),
            )
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
        # history
        evo = evo if self.caught else "-----"
        lab10: Any = menu.add.label(
            title=evo,
            label_id="history",
            font_size=self.font_size_small,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab10.translate(fix_measure(width, 0.01), fix_measure(height, 0.76))

        # history monsters
        if self.caught:
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
        _path = f"gfx/sprites/battle/{monster.slug}-front.png"
        _path = _path if self.caught else prepare.MISSING_IMAGE
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(_path),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_measure(width, 0.20), fix_measure(height, 0.05)
        )

    def __init__(self, **kwargs: Any) -> None:
        monster: Optional[MonsterModel] = None
        for element in kwargs.values():
            monster = element["monster"]
        if monster is None:
            raise ValueError("No monster")
        width, height = prepare.SCREEN_SIZE
        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                prepare.BG_JOURNAL_INFO
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        checks = local_session.player.tuxepedia.get(monster.slug)
        self.caught = True if checks == SeenStatus.caught else False
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
        client = self.client
        monsters = list(local_session.player.tuxepedia)
        box: list[MonsterModel] = []
        for mov in monsters:
            results = db.lookup(mov, table="monster")
            box.append(results)
        box = sorted(box, key=lambda x: x.txmn_id)
        param: dict[str, Any] = {}
        if event.button == buttons.RIGHT and event.pressed and box:
            slot = box.index(self._monster)
            if slot < (len(box) - 1):
                slot += 1
                param["monster"] = box[slot]
                client.replace_state("JournalInfoState", kwargs=param)
            else:
                param["monster"] = box[0]
                client.replace_state("JournalInfoState", kwargs=param)
        elif event.button == buttons.LEFT and event.pressed and box:
            slot = box.index(self._monster)
            if slot > 0:
                slot -= 1
                param["monster"] = box[slot]
                client.replace_state("JournalInfoState", kwargs=param)
            else:
                param["monster"] = box[len(box) - 1]
                client.replace_state("JournalInfoState", kwargs=param)
        elif (
            event.button == buttons.BACK
            or event.button == buttons.B
            or event.button == buttons.A
        ) and event.pressed:
            client.pop_state()
        return None
