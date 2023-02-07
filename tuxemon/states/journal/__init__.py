# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import math
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Sequence

import pygame_menu
from pygame_menu import baseimage, locals, widgets

from tuxemon import formula, graphics, prepare
from tuxemon.db import SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.session import local_session

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tuxemon.monster import Monster

MAX_PAGE = 20


MenuGameObj = Callable[[], object]


def fix_width(screen_x: int, pos_x: float) -> int:
    """it returns the correct width based on percentage"""
    value = round(screen_x * pos_x)
    return value


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class JournalChoice(PygameMenuState):
    """Shows the pages."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: Sequence[Monster],
    ) -> None:
        width = menu._width
        height = menu._height

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        total_monster = len(monsters)
        # defines number of pages based on the total nr of monsters
        # it uses math.ceil because if the diff is < .5 , it must
        # round up (eg. 11.49 > 12)
        diff = math.ceil(total_monster / MAX_PAGE)
        menu._column_max_width = [
            fix_width(width, 0.33),
            fix_width(width, 0.33),
        ]

        for lab in range(diff):
            maximum = (lab * MAX_PAGE) + MAX_PAGE
            minimum = lab * MAX_PAGE
            label = T.format(
                "page_tuxepedia", {"a": str(minimum), "b": str(maximum)}
            ).upper()
            menu.add.button(
                label,
                change_state(
                    "JournalState", kwargs={"slug": monsters, "page": lab}
                ),
                font_size=15,
            ).translate(fix_width(width, 0.25), fix_height(height, 0.01))

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/tux_generic.png"
            ),
            drawing_position=baseimage.POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_LEFT

        columns = 2

        monsters = list(db.database["monster"])
        box = []
        for mov in monsters:
            results = db.lookup(mov, table="monster")
            if results.txmn_id > 0:
                box.append(results)

        diff = round(len(box) / MAX_PAGE) + 1
        rows = int(diff / columns) + 1

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        menu_items_map = []
        menu_items_map = box

        self.add_menu_items(self.menu, menu_items_map)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = PygameMenuState.background_color
        theme.widget_alignment = locals.ALIGN_LEFT


class JournalState(PygameMenuState):
    """Shows monsters in a single page."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: Sequence[Monster],
    ) -> None:
        width = menu._width
        height = menu._height
        menu._column_max_width = [
            fix_width(width, 0.33),
            fix_width(width, 0.33),
        ]

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        monsters = sorted(monsters, key=lambda x: x.txmn_id)

        player = local_session.player
        for mon in monsters:
            font_color = (105, 105, 105)
            click_on = None
            if mon.slug in player.tuxepedia:
                if player.tuxepedia[mon.slug] == SeenStatus.seen:
                    font_color = (25, 25, 112, 1)
                    click_on = change_state(
                        "JournalInfoState", kwargs={"slug": mon.slug}
                    )
                elif player.tuxepedia[mon.slug] == SeenStatus.caught:
                    font_color = (0, 0, 0, 1)
                    click_on = change_state(
                        "JournalInfoState", kwargs={"slug": mon.slug}
                    )
                label = str(mon.txmn_id) + ". " + T.translate(mon.slug).upper()
                menu.add.button(
                    label,
                    click_on,
                    font_size=15,
                    font_color=font_color,
                    selection_color=font_color,
                ).translate(fix_width(width, 0.25), fix_height(height, 0.01))
            else:
                label = str(mon.txmn_id) + ". " + T.translate(mon.slug).upper()
                menu.add.label(
                    label,
                    font_size=15,
                    font_color=font_color,
                ).translate(fix_width(width, 0.25), fix_height(height, 0.01))

    def __init__(self, **kwargs) -> None:
        mon = ""
        chapter = ""
        for ele in kwargs.values():
            mon = ele["slug"]
            chapter = ele["page"]

        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/tux_generic.png"
            ),
            drawing_position=baseimage.POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_LEFT

        columns = 2

        # defines range txmn_ids
        min_txmn = ""
        max_txmn = ""
        if chapter == 0:
            min_txmn = 0
            max_txmn = MAX_PAGE
        else:
            min_txmn = chapter * MAX_PAGE
            max_txmn = (chapter + 1) * MAX_PAGE

        # applies range to tuxemon
        box = []
        for ele in mon:
            if min_txmn < ele.txmn_id <= max_txmn:
                box.append(ele)

        # fix columns and rows
        num_mon = ""
        if len(box) != MAX_PAGE:
            num_mon = len(box) + 1
        else:
            num_mon = len(box)
        rows = num_mon / columns

        super().__init__(
            height=height, width=width, columns=columns, rows=int(rows)
        )

        self.add_menu_items(self.menu, box)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = PygameMenuState.background_color
        theme.widget_alignment = locals.ALIGN_LEFT


class JournalInfoState(PygameMenuState):
    """Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        slug: str,
    ) -> None:
        width = menu._width
        height = menu._height

        data = db.lookup(slug, table="monster")
        name = T.translate(data.slug).upper()
        desc = T.translate(f"{data.slug}_description")
        # evolution
        evo = ""
        if data.evolutions:
            if len(data.evolutions) == 1:
                evo = T.translate("yes_evolution")
            else:
                evo = T.translate("yes_evolutions")
        else:
            evo = T.translate("no_evolution")
        # types
        types = ""
        if len(data.types) == 1:
            types = T.translate(data.types[0])
        else:
            types = (
                T.translate(data.types[0]) + " " + T.translate(data.types[1])
            )
        # weight and height
        if prepare.CONFIG.unit == "metric":
            mon_weight = data.weight
            mon_height = data.height
            unit_weight = "kg"
            unit_height = "cm"
        else:
            mon_weight = formula.convert_lbs(data.weight)
            mon_height = formula.convert_ft(data.height)
            unit_weight = "lb"
            unit_height = "ft"
        # name
        menu._auto_centering = False
        menu.add.label(
            title=name,
            label_id="name",
            font_size=30,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.15))
        # weight
        menu.add.label(
            title=str(mon_weight) + " " + unit_weight,
            label_id="weight",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.25))
        # height
        menu.add.label(
            title=str(mon_height) + " " + unit_height,
            label_id="height",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.65), fix_height(height, 0.25))
        # type
        menu.add.label(
            title=types,
            label_id="type",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.30))
        # shape
        menu.add.label(
            title=T.translate(data.shape),
            label_id="shape",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.35))
        # txmn_id
        menu.add.label(
            title="ID: " + str(data.txmn_id),
            label_id="txmn_id",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.10))
        # description
        menu.add.label(
            title=desc,
            label_id="description",
            font_size=15,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.01), fix_height(height, 0.56))
        # evolution
        menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=15,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.01), fix_height(height, 0.76))
        # open evolution monster
        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        # evolution monsters buttons
        f = menu.add.frame_h(
            float=True,
            width=fix_width(width, 0.95),
            height=fix_width(width, 0.05),
            frame_id="evolutions",
        )
        f.translate(0, fix_height(height, 0.80))
        f._relax = True
        # removes duplicates
        player = local_session.player
        elements = []
        for ele in data.evolutions:
            if ele.monster_slug in player.tuxepedia:
                elements.append(ele.monster_slug)
        no_duplicates = sorted(set(elements))
        labels = [
            menu.add.button(
                title=f"{T.translate(ele).upper()}",
                action=change_state("JournalInfoState", kwargs={"slug": ele}),
                align=locals.ALIGN_LEFT,
                font_size=14,
                selection_effect=widgets.HighlightSelection(),
            )
            for ele in no_duplicates
        ]
        for no_duplicates in labels:
            f.pack(no_duplicates)
        # image
        new_image = pygame_menu.BaseImage(
            graphics.transform_resource_filename(
                f"gfx/sprites/battle/{data.slug}-front.png"
            ),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_width(width, 0.20), fix_height(height, 0.05)
        )

    def __init__(self, **kwargs) -> None:
        mon = ""
        for ele in kwargs.values():
            mon = ele["slug"]

        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/tux_info.png"
            ),
            drawing_position=baseimage.POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu, mon)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = PygameMenuState.background_color
        theme.widget_alignment = locals.ALIGN_LEFT


class MonsterInfoState(PygameMenuState):
    """Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        data: Monster,
    ) -> None:
        width = menu._width
        height = menu._height

        name = T.translate(data.slug).upper()
        desc = T.translate(f"{data.slug}_description")
        # evolution
        evo = ""
        if data.evolutions:
            if len(data.evolutions) == 1:
                evo = T.translate("yes_evolution")
            else:
                evo = T.translate("yes_evolutions")
        else:
            evo = T.translate("no_evolution")
        # types
        types = ""
        if data.type2 is not None:
            types = T.translate(data.type1) + " " + T.translate(data.type2)
        else:
            types = T.translate(data.type1)
        # weight and height
        if prepare.CONFIG.unit == "metric":
            mon_weight = data.weight
            mon_height = data.height
            unit_weight = "kg"
            unit_height = "cm"
        else:
            mon_weight = formula.convert_lbs(data.weight)
            mon_height = formula.convert_ft(data.height)
            unit_weight = "lb"
            unit_height = "ft"
        # name + lv
        menu._auto_centering = False
        menu.add.label(
            title=name,
            label_id="name",
            font_size=20,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.15))
        # level
        menu.add.label(
            title="Lv. " + str(data.level),
            label_id="level",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.20))
        # exp
        exp = data.total_experience
        exp_lv = data.experience_required(1) - data.total_experience
        lv = data.level + 1
        menu.add.label(
            title=T.format(
                "tuxepedia_exp", {"exp": exp, "exp_lv": exp_lv, "lv": lv}
            ),
            label_id="exp",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.25))
        # weight
        menu.add.label(
            title=str(mon_weight) + " " + unit_weight,
            label_id="weight",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.30))
        # height
        menu.add.label(
            title=str(mon_height) + " " + unit_height,
            label_id="height",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.65), fix_height(height, 0.30))
        # type
        menu.add.label(
            title=types,
            label_id="type",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.35))
        # shape
        menu.add.label(
            title=T.translate(data.shape),
            label_id="shape",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.40))
        # capture
        doc = formula.today_ordinal() - data.capture
        menu.add.label(
            title=T.format("tuxepedia_capture", {"doc": doc}),
            label_id="capture",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.45))
        # txmn_id
        menu.add.label(
            title="ID: " + str(data.txmn_id),
            label_id="txmn_id",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.50), fix_height(height, 0.10))
        # description
        menu.add.label(
            title=desc,
            label_id="description",
            font_size=15,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.01), fix_height(height, 0.56))
        # evolution
        menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=15,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        ).translate(fix_width(width, 0.01), fix_height(height, 0.76))
        # open evolution monster
        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        # evolution monsters buttons
        f = menu.add.frame_h(
            float=True,
            width=fix_width(width, 0.95),
            height=fix_width(width, 0.05),
            frame_id="evolutions",
        )
        f.translate(0, fix_height(height, 0.80))
        f._relax = True
        # removes duplicates
        player = local_session.player
        elements = []
        for ele in data.evolutions:
            if ele.monster_slug in player.tuxepedia:
                elements.append(ele.monster_slug)
        no_duplicates = sorted(set(elements))
        labels = [
            menu.add.button(
                title=f"{T.translate(ele).upper()}",
                action=change_state("JournalInfoState", kwargs={"slug": ele}),
                align=locals.ALIGN_LEFT,
                font_size=14,
                selection_effect=widgets.HighlightSelection(),
            )
            for ele in no_duplicates
        ]
        for no_duplicates in labels:
            f.pack(no_duplicates)
        # image
        new_image = pygame_menu.BaseImage(
            graphics.transform_resource_filename(data.front_battle_sprite),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_width(width, 0.20), fix_height(height, 0.05)
        )

    def __init__(self, **kwargs) -> None:
        mon = ""
        for ele in kwargs.values():
            mon = ele["slug"]

        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=graphics.transform_resource_filename(
                "gfx/ui/item/tux_info.png"
            ),
            drawing_position=baseimage.POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu, mon)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = PygameMenuState.background_color
        theme.widget_alignment = locals.ALIGN_LEFT
