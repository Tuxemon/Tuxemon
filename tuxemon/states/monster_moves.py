# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, Optional

import pygame_menu
from pygame_menu import locals
from pygame_menu.widgets.widget.label import Label
from pygame_menu.widgets.widget.progressbar import ProgressBar

from tuxemon import prepare
from tuxemon.db import MonsterModel, SpeedLabel, db
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const import buttons
from tuxemon.technique.technique import Technique
from tuxemon.tools import fix_measure

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.platform.events import PlayerInput

lookup_cache: dict[str, MonsterModel] = {}


def _lookup_monsters() -> None:
    global lookup_cache
    lookup_cache = {
        mon_name: result
        for mon_name in db.database["monster"]
        if (result := MonsterModel.lookup(mon_name, db)).txmn_id > 0
    }


class MonsterMovesState(PygameMenuState):
    """
    Shows details of the single monster with the journal background graphic.
    """

    name: ClassVar[str] = "MonsterMovesState"
    description_label: Optional[Any] = None
    info_label: Optional[Any] = None
    bar_accuracy: Optional[ProgressBar] = None
    bar_potency: Optional[ProgressBar] = None
    power_label: Optional[Any] = None
    range_icon_widget: Optional[Any] = None
    speed_icon_widget: Optional[Any] = None
    type_icon_widgets: list[Any] = []

    # -------------------------
    # Top section (static per monster)
    # -------------------------
    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monster: Monster,
    ) -> None:
        fxw: Callable[[float], int] = lambda r: fix_measure(menu._width, r)
        fxh: Callable[[float], int] = lambda r: fix_measure(menu._height, r)
        menu._width = fxw(248 / 256)

        # Name (white, manual position)
        menu._auto_centering = False
        lab1: Any = menu.add.label(
            title=f"{monster.txmn_id}. {monster.name.upper()}",
            label_id=monster.slug,
            font_color=(255, 255, 255),  # white
            font_size=self.font_type.biggest,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fxw(79.4 / 256), fxh(-0.2 / 144))

        # Move buttons (manual positions; uppercase names)
        moveset: list[Technique] = monster.moves.get_moves()
        output = sorted(moveset, key=lambda x: x.tech_id)

        _height = 4.8 / 144
        for tech in output:
            _height += 12 / 144
            menu.add.button(
                title=tech.name.upper(),
                action=None,
                button_id=tech.slug,
                font_size=self.font_type.biggest,
                align=locals.ALIGN_LEFT,
                float=True,
            ).translate(fxw(83.6 / 256), fxh(_height))

        # Monster image (manual position)
        new_image = self._create_image(monster.sprite_handler.front_path)
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(fxw(1 / 256), fxh(2 / 144))

    # -------------------------
    # Per-tech UI updates
    # -------------------------
    def add_menu_technique(self, menu: pygame_menu.Menu, slug: str) -> None:
        # keep width stable across updates
        menu._width = fix_measure(prepare.SCREEN_SIZE[0], 248 / 256)

        technique = Technique.create(slug)

        # Structure from baseline (re-usable widgets), plus your custom pieces
        self._add_description_label(menu, technique)
        self._add_progress_bars(
            menu, technique
        )  # accuracy/potency with manual placement
        self._add_icons(menu, technique)  # type icons, range icon, speed icon
        self._add_power_label(
            menu, technique
        )  # power % label (manual placement)

    # -------- description ----------
    def _add_description_label(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        description_label: Optional[Label] = None
        for widget in menu.get_widgets():
            if isinstance(widget, Label) and widget.get_id() == "description":
                description_label = widget
                break

        if description_label is None:
            self.description_label = menu.add.label(
                title=technique.description,
                label_id="description",
                font_size=self.font_type.bigger,
                wordwrap=True,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            assert not isinstance(self.description_label, list)
            self.description_label.translate(
                fix_measure(width, 3.8 / 256), fix_measure(height, 113 / 144)
            )
        else:
            description_label.set_title(technique.description)

    # -------- info line (id/types/recharge) ----------
    def _add_info_label(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        info_label: Optional[Label] = None
        for widget in menu.get_widgets():
            if isinstance(widget, Label) and widget.get_id() == "label":
                info_label = widget
                break

        types_text = " ".join(
            map(lambda s: T.translate(s.slug), technique.types.current)
        )
        label_text = T.format(
            "technique_id_types_recharge",
            {
                "id": technique.tech_id,
                "types": types_text,
                "rec": str(technique.recharge_length),
            },
        )

        if info_label is None:
            self.info_label = menu.add.label(
                title=label_text,
                label_id="label",
                font_size=self.font_type.small,
                wordwrap=True,
                align=locals.ALIGN_LEFT,
                float=True,
            )
            # place it just above the description block
            assert not isinstance(self.info_label, list)
            self.info_label.translate(
                fix_measure(width, 206 / 256), fix_measure(height, 102 / 144)
            )
        else:
            info_label.set_title(label_text)

    # -------- bars ----------
    def _add_progress_bars(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE

        diff_accuracy = round(
            (technique.accuracy / prepare.ACCURACY_RANGE[1]) * 100
        )
        diff_potency = round(
            (technique.potency / prepare.POTENCY_RANGE[1]) * 100
        )

        # Find existing bars (by title) if present
        bar_accuracy: Optional[ProgressBar] = None
        bar_potency: Optional[ProgressBar] = None
        for widget in menu.get_widgets():
            if isinstance(widget, ProgressBar):
                if widget.get_title() == T.translate("technique_accuracy"):
                    bar_accuracy = widget
                elif widget.get_title() == T.translate("technique_potency"):
                    bar_potency = widget

        # Accuracy (manual placement)
        if bar_accuracy is None:
            self.bar_accuracy = menu.add.progress_bar(
                T.translate("technique_accuracy"),
                default=diff_accuracy,
                font_size=self.font_type.biggest,
                width=fix_measure(width, 80 / 256),
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.bar_accuracy.translate(
                fix_measure(width, 4 / 256), fix_measure(height, 74.8 / 144)
            )
        else:
            bar_accuracy.set_value(diff_accuracy)

        # Potency (manual placement)
        if bar_potency is None:
            self.bar_potency = menu.add.progress_bar(
                T.translate("technique_potency"),
                default=diff_potency,
                font_size=self.font_type.biggest,
                width=fix_measure(width, 80 / 256),
                align=locals.ALIGN_LEFT,
                float=True,
            )
            self.bar_potency.translate(
                fix_measure(width, 4 / 256), fix_measure(height, 99.8 / 144)
            )
        else:
            bar_potency.set_value(diff_potency)

    # -------- icons (types, range, speed) ----------
    def _add_icons(self, menu: pygame_menu.Menu, technique: Technique) -> None:
        # Ensure attributes exist
        if not hasattr(self, "type_icon_widgets"):
            self.type_icon_widgets: list[Any] = []
        if not hasattr(self, "range_icon_widget"):
            self.range_icon_widget: Optional[Any] = None
        if not hasattr(self, "speed_icon_widget"):
            self.speed_icon_widget: Optional[Any] = None

        fxw: Callable[[float], int] = lambda r: fix_measure(
            prepare.SCREEN_SIZE[0], r
        )
        fxh: Callable[[float], int] = lambda r: fix_measure(
            prepare.SCREEN_SIZE[1], r
        )

        # Clear previous type icons (remove from menu, not just hide)
        for w in self.type_icon_widgets:
            if w in menu.get_widgets():
                menu.remove_widget(w)
        self.type_icon_widgets.clear()

        # Clear previous range icon
        if (
            self.range_icon_widget is not None
            and self.range_icon_widget in menu.get_widgets()
        ):
            menu.remove_widget(self.range_icon_widget)
        self.range_icon_widget = None

        # Clear previous speed icon
        if (
            self.speed_icon_widget is not None
            and self.speed_icon_widget in menu.get_widgets()
        ):
            menu.remove_widget(self.speed_icon_widget)
        self.speed_icon_widget = None

        # Type icons (manual placement; up to 2)
        if technique.types.current:
            x_positions = [
                225 / 256,
                213.4 / 256,
            ]  # second slightly left of first
            y_position = 73.8 / 144
            for i, t in enumerate(technique.types.current[:2]):
                path = f"gfx/ui/icons/element/{t.name.lower()}_type_small.png"
                img = self._create_image(path)
                img.scale(prepare.SCALE, prepare.SCALE)
                icon = menu.add.image(img.copy(), float=True)
                icon.translate(fxw(x_positions[i]), fxh(y_position))
                self.type_icon_widgets.append(icon)

        # Range icon
        if technique.range:
            path = f"gfx/ui/icons/range/{technique.range.name.lower()}.png"
            rimg = self._create_image(path)
            rimg.scale(prepare.SCALE, prepare.SCALE)
            self.range_icon_widget = menu.add.image(rimg.copy(), float=True)
            self.range_icon_widget.translate(fxw(4 / 256), fxh(86.8 / 144))

        # Speed icon
        speed_label = SpeedLabel.from_numeric(technique.speed)
        speed_key = speed_label.value

        spath = f"gfx/ui/icons/speed/{speed_key}.png"
        simg = self._create_image(spath)
        simg.scale(prepare.SCALE, prepare.SCALE)
        self.speed_icon_widget = menu.add.image(simg.copy(), float=True)
        self.speed_icon_widget.translate(fxw(222 / 256), fxh(51.8 / 144))

    # -------- power label ----------
    def _add_power_label(
        self, menu: pygame_menu.Menu, technique: Technique
    ) -> None:
        width, height = prepare.SCREEN_SIZE
        power_percent = round(technique.power * 100)
        power_text = f"{T.translate('technique_power')} {power_percent}%"

        # Remove old label if present
        if (
            hasattr(self, "power_label")
            and self.power_label in menu.get_widgets()
        ):
            menu.remove_widget(self.power_label)

        # Create fresh
        self.power_label = menu.add.label(
            title=power_text,
            font_size=self.font_type.biggest,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(self.power_label, list)
        self.power_label.translate(
            fix_measure(width, 42 / 256), fix_measure(height, 87.8 / 144)
        )

    # -------------------------
    # Lifecycle / plumbing
    # -------------------------
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
        theme = self._setup_theme(prepare.TECH_INFO)
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
            monsters = _get_monsters(self._monster, self._source)
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


def _get_monsters(monster: Monster, source: str) -> list[Monster]:
    owner = monster.get_owner()
    if source == "MonsterTakeState":
        box = owner.monster_boxes.get_box_name(monster.instance_id)
        if box is None:
            raise ValueError("Box doesn't exist")
        return owner.monster_boxes.get_monsters(box)
    else:
        return owner.monsters
