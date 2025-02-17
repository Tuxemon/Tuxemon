# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from typing import Any, Optional

import pygame_menu
import pygame_menu.widgets
import pygame_menu.widgets.core
import pygame_menu.widgets.core.widget
import pygame_menu.widgets.widget
import pygame_menu.widgets.widget.label
import pygame_menu.widgets.widget.progressbar
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.db import MonsterModel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster import Monster
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.technique.technique import Technique

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


class MonsterMovesState(PygameMenuState):
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

        # name
        menu._auto_centering = False
        lab1: Any = menu.add.label(
            title=f"{monster.txmn_id}. {monster.name.upper()}",
            label_id=monster.slug,
            font_size=self.font_size_small,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fix_measure(width, 0.50), fix_measure(height, 0.10))
        # moves
        moveset: list[Technique] = []
        moveset = monster.moves
        output = sorted(moveset, key=lambda x: x.tech_id)

        _height = 0.10
        for tech in output:
            _height += 0.05
            menu.add.button(
                title=tech.name,
                action=None,
                button_id=tech.slug,
                font_size=self.font_size_small,
                align=locals.ALIGN_LEFT,
                float=True,
            ).translate(fix_measure(width, 0.50), fix_measure(height, _height))

        # image
        new_image = self._create_image(monster.front_battle_sprite)
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_measure(width, 0.20), fix_measure(height, 0.05)
        )

    def add_menu_technique(self, menu: pygame_menu.Menu, slug: str) -> None:
        width, height = prepare.SCREEN_SIZE
        menu._width = fix_measure(width, 0.97)

        technique = Technique()
        technique.load(slug)

        self._add_description_label(menu, technique)
        self._add_info_label(menu, technique)
        self._add_progress_bars(menu, technique)

    def _add_description_label(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        description_label = None
        for widget in menu.get_widgets():
            if (
                isinstance(widget, pygame_menu.widgets.widget.label.Label)
                and widget.get_id() == "description"
            ):
                description_label = widget
                break
        if description_label is None:
            self.description_label: Any = menu.add.label(
                title=technique.description,
                label_id="description",
                font_size=self.font_size_small,
                wordwrap=True,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.description_label.translate(
                fix_measure(width, 0.01), fix_measure(height, 0.56)
            )
        else:
            description_label.set_title(technique.description)

    def _add_info_label(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        info_label = None
        for widget in menu.get_widgets():
            if (
                isinstance(widget, pygame_menu.widgets.widget.label.Label)
                and widget.get_id() == "label"
            ):
                info_label = widget
                break
        types = " ".join(map(lambda s: T.translate(s.slug), technique.types))
        label = T.format(
            "technique_id_types_recharge",
            {
                "id": technique.tech_id,
                "types": types,
                "rec": str(technique.recharge_length),
            },
        )
        if info_label is None:
            self.info_label: Any = menu.add.label(
                title=label,
                label_id="label",
                font_size=self.font_size_small,
                wordwrap=True,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.info_label.translate(
                fix_measure(width, 0.01), fix_measure(height, 0.70)
            )
        else:
            info_label.set_title(label)

    def _add_progress_bars(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        bar_power = None
        bar_accuracy = None
        bar_potency = None
        for widget in menu.get_widgets():
            if isinstance(
                widget, pygame_menu.widgets.widget.progressbar.ProgressBar
            ):
                if widget.get_title() == T.translate("technique_power"):
                    bar_power = widget
                elif widget.get_title() == T.translate("technique_accuracy"):
                    bar_accuracy = widget
                elif widget.get_title() == T.translate("technique_potency"):
                    bar_potency = widget

        diff_power = round((technique.power / prepare.POWER_RANGE[1]) * 100, 1)
        diff_accuracy = round(
            (technique.accuracy / prepare.ACCURACY_RANGE[1]) * 100, 1
        )
        diff_potency = round(
            (technique.potency / prepare.POTENCY_RANGE[1]) * 100, 1
        )

        if bar_power is None:
            self.bar_power: Any = menu.add.progress_bar(
                T.translate("technique_power"),
                default=diff_power,
                font_size=self.font_size_small,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.bar_power.translate(
                fix_measure(width, 0.01), fix_measure(height, 0.75)
            )
        else:
            bar_power.set_default_value(diff_power)

        if bar_accuracy is None:
            self.bar_accuracy: Any = menu.add.progress_bar(
                T.translate("technique_accuracy"),
                default=diff_accuracy,
                font_size=self.font_size_small,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.bar_accuracy.translate(
                fix_measure(width, 0.28), fix_measure(height, 0.75)
            )
        else:
            bar_accuracy.set_default_value(diff_accuracy)

        if bar_potency is None:
            self.bar_potency: Any = menu.add.progress_bar(
                T.translate("technique_potency"),
                default=diff_potency,
                font_size=self.font_size_small,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.bar_potency.translate(
                fix_measure(width, 0.58), fix_measure(height, 0.75)
            )
        else:
            bar_potency.set_default_value(diff_potency)

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
        self.update_selected_widget()
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
                client.replace_state("MonsterMovesState", kwargs=param)
            elif event.button == buttons.LEFT and event.pressed:
                slot = (slot - 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterMovesState", kwargs=param)
            else:
                self.update_selected_widget()
                menu = self.menu.get_current()
                if self.selected_widget:
                    self.add_menu_technique(
                        menu, self.selected_widget.get_id()
                    )
                return super().process_event(event)

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
