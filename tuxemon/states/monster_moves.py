# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, ALIGN_LEFT, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.widgets.widget.label import Label
from pygame_menu.widgets.widget.progressbar import ProgressBar

from tuxemon.db import SpeedLabel
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster.renderer import MonsterRenderer
from tuxemon.platform.const import buttons
from tuxemon.platform.const.graphics import TECH_INFO
from tuxemon.platform.const.sizes import ACCURACY_RANGE, POTENCY_RANGE
from tuxemon.technique.technique import Technique
from tuxemon.tools import (
    fix_measure,
    open_dialog,
    scale,
    transform_resource_filename,
)

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.monster.monster import Monster
    from tuxemon.platform.events import PlayerInput


class MonsterMovesState(PygameMenuState):
    """
    Shows details of the single monster with the journal background graphic.
    """

    name: ClassVar[str] = "MonsterMovesState"
    description_label: Any | None = None
    info_label: Any | None = None
    bar_accuracy: ProgressBar | None = None
    bar_potency: ProgressBar | None = None
    _on_selection: Callable[[Technique], None] | None = None
    _is_valid_entry: Callable[[Technique | None], bool] | None = None

    # -------------------------
    # Top section (static per monster)
    # -------------------------
    def add_menu_items(
        self,
        menu: Menu,
        monster: Monster,
    ) -> None:
        def fxw(r: float) -> int:
            return fix_measure(menu._width, r)

        def fxh(r: float) -> int:
            return fix_measure(menu._height, r)

        menu._width = fxw(248 / 256)

        self.minimal_font = transform_resource_filename(
            "font", self.client.config.locale.minimal_font_file
        )

        # Name (white, manual position)
        menu._auto_centering = False
        lab1: Any = menu.add.label(
            title=f"{monster.txmn_id}. {monster.name.upper()}",
            label_id=monster.slug,
            font_color=(255, 255, 255),  # white
            font_size=self.font_type.biggest,
            align=ALIGN_LEFT,
            float=True,
        )
        lab1.translate(fxw(79.4 / 256), fxh(-0.2 / 144))

        # Move buttons (newest is always last)
        output: list[Technique] = monster.moves.get_moves()

        step = 9 / 144 if len(output) >= 5 else 12 / 144
        _height = 4.8 / 144
        for tech in output:
            _height += step
            menu.add.button(
                title=tech.name.upper(),
                action=None,
                button_id=tech.slug,
                font_size=self.font_type.biggest,
                align=ALIGN_LEFT,
                float=True,
            ).translate(fxw(83.6 / 256), fxh(_height))

        # Monster image (manual position)
        renderer = MonsterRenderer(monster, scale=self.factor)
        surface = renderer.get_sprite("front").image
        new_image = self._create_image_from_surface(surface)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(fxw(1 / 256), fxh(2 / 144))

    # -------------------------
    # Per-tech UI updates
    # -------------------------
    def add_menu_technique(self, menu: Menu, slug: str) -> None:
        # keep width stable across updates
        width, height = self.client.context.resolution
        menu._width = fix_measure(width, 248 / 256)

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
    def _add_description_label(self, menu: Menu, technique: Technique) -> None:
        width, height = self.client.context.resolution
        description_label: Label | None = None
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
                align=ALIGN_LEFT,
                float=True,
            )
            assert not isinstance(self.description_label, list)
            self.description_label.translate(
                fix_measure(width, 3.8 / 256), fix_measure(height, 113 / 144)
            )
        else:
            description_label.set_title(technique.description)

    # -------- info line (id/types/recharge) ----------
    def _add_info_label(self, menu: Menu, technique: Technique) -> None:
        width, height = self.client.context.resolution
        info_label: Label | None = None
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
                "rec": str(technique.cooldown.duration),
            },
        )

        if info_label is None:
            self.info_label = menu.add.label(
                title=label_text,
                label_id="label",
                font_size=self.font_type.small,
                wordwrap=True,
                align=ALIGN_LEFT,
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
    def _add_progress_bars(self, menu: Menu, technique: Technique) -> None:
        width, height = self.client.context.resolution

        diff_accuracy = round((technique.accuracy / ACCURACY_RANGE[1]) * 100)
        diff_potency = round((technique.potency / POTENCY_RANGE[1]) * 100)
        show_potency = diff_potency > 0

        # Find existing bars (by title) if present
        bar_accuracy: ProgressBar | None = None
        bar_potency: ProgressBar | None = None
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
                align=ALIGN_LEFT,
                progress_text_font=self.minimal_font,
                float=True,
                box_border_width=scale(1),
                progress_text_font_hfactor=1.0,
            )
            self.bar_accuracy.translate(
                fix_measure(width, 4 / 256), fix_measure(height, 74.8 / 144)
            )
        else:
            bar_accuracy.set_value(diff_accuracy)

        # Potency (manual placement) — omit entirely when potency is 0%
        if not show_potency:
            if bar_potency is not None:
                menu.remove_widget(bar_potency)
                self.bar_potency = None
        elif bar_potency is None:
            self.bar_potency = menu.add.progress_bar(
                T.translate("technique_potency"),
                default=diff_potency,
                font_size=self.font_type.biggest,
                width=fix_measure(width, 80 / 256),
                align=ALIGN_LEFT,
                progress_text_font=self.minimal_font,
                float=True,
                progress_text_font_hfactor=1.0,
                box_border_width=scale(1),
            )
            self.bar_potency.translate(
                fix_measure(width, 4 / 256), fix_measure(height, 99.8 / 144)
            )
        else:
            bar_potency.set_value(diff_potency)

    # -------- icons (types, range, speed) ----------
    def _add_icons(self, menu: Menu, technique: Technique) -> None:

        width, height = self.client.context.resolution

        def fxw(r: float) -> int:
            return fix_measure(width, r)

        def fxh(r: float) -> int:
            return fix_measure(height, r)

        # Type icons: two fixed slots (type_icon_0, type_icon_1)
        x_positions = [225 / 256, 213.4 / 256]
        y_position = 73.8 / 144
        for i in range(2):
            slot_id = f"type_icon_{i}"
            existing = menu.get_widget(slot_id)
            if i < len(technique.types.current):
                t = technique.types.current[i]
                path = f"gfx/ui/icons/element/{t.name.lower()}_type_small.png"
                img = self._create_image(path)
                img.scale(self.factor, self.factor)
                if existing is None:
                    icon = menu.add.image(img.copy(), image_id=slot_id, float=True)
                    icon.translate(fxw(x_positions[i]), fxh(y_position))
                else:
                    existing.set_image(img)
                    existing.show()
            else:
                if existing is not None:
                    existing.hide()

        # Range icon
        existing_range = menu.get_widget("range_icon")
        if technique.range:
            path = f"gfx/ui/icons/range/{technique.range.name.lower()}.png"
            rimg = self._create_image(path)
            rimg.scale(self.factor, self.factor)
            if existing_range is None:
                w = menu.add.image(rimg.copy(), image_id="range_icon", float=True)
                w.translate(fxw(4 / 256), fxh(86.8 / 144))
            else:
                existing_range.set_image(rimg)
                existing_range.show()
        elif existing_range is not None:
            existing_range.hide()

        # Speed icon
        speed_label = SpeedLabel.from_numeric(technique.speed)
        speed_key = speed_label.value
        spath = f"gfx/ui/icons/speed/{speed_key}.png"
        simg = self._create_image(spath)
        simg.scale(self.factor, self.factor)
        existing_speed = menu.get_widget("speed_icon")
        if existing_speed is None:
            w = menu.add.image(simg.copy(), image_id="speed_icon", float=True)
            w.translate(fxw(222 / 256), fxh(51.8 / 144))
        else:
            existing_speed.set_image(simg)

    # -------- power label ----------
    def _add_power_label(self, menu: Menu, technique: Technique) -> None:
        width, height = self.client.context.resolution
        power_percent = round(technique.power * 100)
        power_text = f"{T.translate('technique_power')} {power_percent}%"

        existing = menu.get_widget("power_label")
        if existing is None:
            label = menu.add.label(
                title=power_text,
                label_id="power_label",
                font_size=self.font_type.biggest,
                align=ALIGN_LEFT,
                float=True,
            )
            assert not isinstance(label, list)
            label.translate(
                fix_measure(width, 42 / 256), fix_measure(height, 87.8 / 144)
            )
        else:
            existing.set_title(power_text)

    # -------------------------
    # Lifecycle / plumbing
    # -------------------------
    def __init__(
        self,
        client: BaseClient,
        monster: Monster,
        source: str,
        monsters: list[Monster] | None,
        on_selection: Callable[[Technique], None] | None = None,
        is_valid_entry: Callable[[Technique | None], bool] | None = None,
        **kwargs: Any,
    ) -> None:

        width, height = client.context.resolution

        self._monster = monster
        self._source = source
        self._monsters = monsters
        self._on_selection = on_selection
        self._is_valid_entry = is_valid_entry

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(TECH_INFO)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.widget_font_shadow = False
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu, monster)
        self.update_selected_widget()
        self.reset_theme()
        if self.selected_widget:
            self.add_menu_technique(self.menu, self.selected_widget.get_id())

    def reset_theme(self) -> None:
        super().reset_theme()
        if self._menu is not None:
            self._menu._theme.widget_font_shadow = False

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        param: dict[str, Any] = {"source": self._source}
        client = self.client

        # Forget-mode: player must pick a technique to forget
        if self._on_selection is not None:
            if event.button == buttons.A and self.valid_press(event):
                self.update_selected_widget()
                if self.selected_widget:
                    slug = self.selected_widget.get_id()
                    technique = next(
                        (
                            t
                            for t in self._monster.moves.get_moves()
                            if t.slug == slug
                        ),
                        None,
                    )
                    if technique is None:
                        return None
                    if self._is_valid_entry is None or self._is_valid_entry(
                        technique
                    ):
                        self._on_selection(technique)
                    else:
                        open_dialog(
                            self.client,
                            [T.translate("tech_cannot_forget")],
                        )
                return None

            result = super().process_event(event)
            self.update_selected_widget()
            if self.selected_widget:
                self.add_menu_technique(self.menu, self.selected_widget.get_id())
            return result


        if self._source in [
            "WorldMenuState",
            "MonsterMenuState",
            "MonsterTakeState",
        ]:
            monsters = self._monsters
            if not monsters:
                return None

            param["monsters"] = monsters

            slot = monsters.index(self._monster)

            # RIGHT → next monster (with repeat)
            if event.button == buttons.RIGHT and self.valid_press(event):
                slot = (slot + 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterMovesState", **param)
                return None

            # LEFT → previous monster (with repeat)
            elif event.button == buttons.LEFT and self.valid_press(event):
                slot = (slot - 1) % len(monsters)
                param["monster"] = monsters[slot]
                client.replace_state("MonsterMovesState", **param)
                return None

            # Everything else → normal menu behavior
            else:
                result = super().process_event(event)
                self.update_selected_widget()
                if self.selected_widget:
                    self.add_menu_technique(
                        self.menu, self.selected_widget.get_id()
                    )
                return result

        return None
