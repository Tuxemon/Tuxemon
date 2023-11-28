# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import Any, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER

from tuxemon import formula, prepare, tools
from tuxemon.db import MonsterModel
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
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

        name = T.translate(monster.slug).upper()
        desc = T.translate(f"{monster.slug}_description")
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
            title=name,
            label_id="name",
            font_size=30,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab1, list)
        lab1.translate(fix_measure(width, 0.50), fix_measure(height, 0.15))
        # weight
        lab2 = menu.add.label(
            title=str(mon_weight) + " " + unit_weight,
            label_id="weight",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab2, list)
        lab2.translate(fix_measure(width, 0.50), fix_measure(height, 0.25))
        # height
        lab3 = menu.add.label(
            title=str(mon_height) + " " + unit_height,
            label_id="height",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab3, list)
        lab3.translate(fix_measure(width, 0.65), fix_measure(height, 0.25))
        # type
        lab4 = menu.add.label(
            title=T.translate("monster_menu_type"),
            label_id="type_label",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab4, list)
        lab4.translate(fix_measure(width, 0.50), fix_measure(height, 0.30))
        type_image_1 = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                f"gfx/ui/icons/element/{monster.types[0].name}_type.png"
            ),
        )
        if len(monster.types) > 1:
            type_image_2 = pygame_menu.BaseImage(
                tools.transform_resource_filename(
                    f"gfx/ui/icons/element/{monster.types[1].name}_type.png"
                ),
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
        lab5 = menu.add.label(
            title=types,
            label_id="type_loaded",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab5, list)
        lab5.translate(fix_measure(width, 0.50), fix_measure(height, 0.35))
        # shape
        shape = (
            T.translate("monster_menu_shape")
            + ": "
            + T.translate(monster.shape)
        )
        lab6 = menu.add.label(
            title=shape,
            label_id="shape",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab6, list)
        lab6.translate(fix_measure(width, 0.50), fix_measure(height, 0.40))
        # species
        spec = T.translate(f"cat_{monster.category}")
        species = T.translate("monster_menu_species") + ": " + spec
        lab7 = menu.add.label(
            title=species,
            label_id="species",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab7, list)
        lab7.translate(fix_measure(width, 0.50), fix_measure(height, 0.45))
        # txmn_id
        lab8 = menu.add.label(
            title="ID: " + str(monster.txmn_id),
            label_id="txmn_id",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab8, list)
        lab8.translate(fix_measure(width, 0.50), fix_measure(height, 0.10))
        # description
        lab9 = menu.add.label(
            title=desc,
            label_id="description",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab9, list)
        lab9.translate(fix_measure(width, 0.01), fix_measure(height, 0.56))
        # history
        lab10 = menu.add.label(
            title=evo,
            label_id="history",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab10, list)
        lab10.translate(fix_measure(width, 0.01), fix_measure(height, 0.76))

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
            tools.transform_resource_filename(
                f"gfx/sprites/battle/{monster.slug}-front.png"
            ),
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

        assert monster
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
            event.button == buttons.BACK
            or event.button == buttons.B
            or event.button == buttons.A
        ) and event.pressed:
            self.client.pop_state()
        return None
