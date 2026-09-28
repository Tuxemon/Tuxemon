# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.sound import SOUND_TYPE_WIDGET_SELECTION

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.menu.transitions import PopInClamped
from tuxemon.platform.const import buttons
from tuxemon.state.state import State

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.platform.events import PlayerInput


class ControlState(PygameMenuState):
    """This state is responsible for the option menu."""

    name: ClassVar[str] = "ControlState"

    def __init__(
        self,
        client: BaseClient,
        *args: Any,
        main_menu: bool = False,
        **kwargs: Any,
    ) -> None:
        self.main_menu = main_menu

        super().__init__(client, *args, transition=PopInClamped(), **kwargs)

        theme = get_theme(self.client.context.scaling)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme

        self.initialize_items(self.menu)
        self.reload_controls()
        self.reset_theme()

    def initialize_items(self, menu: Menu) -> None:
        def change_state(
            state: State | str, **change_state_kwargs: Any
        ) -> Callable[[], State]:
            return partial(
                self.client.push_state, state, **change_state_kwargs
            )

        menu.select_widget(None)

        menu.add.button(
            title=T.translate("menu_up_key").upper(),
            action=change_state("SetKeyState", value="up"),
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("menu_left_key").upper(),
            action=change_state("SetKeyState", value="left"),
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("menu_right_key").upper(),
            action=change_state("SetKeyState", value="right"),
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("menu_down_key").upper(),
            action=change_state("SetKeyState", value="down"),
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("menu_primary_select_key").upper(),
            action=change_state("SetKeyState", value="a"),
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("menu_secondary_select_key").upper(),
            action=change_state("SetKeyState", value="b"),
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("menu_back_key").upper(),
            action=change_state("SetKeyState", value="back"),
            font_size=self.font_type.small,
        )

        menu.add.button(
            title=T.translate("menu_reset_default").upper(),
            action=self.client.config.reset_controls_to_default,
            font_size=self.font_type.small,
        )

        language = T.translate("menu_language").upper()
        menu.add.button(
            title=f"{language}: {self.client.config.locale.slug}",
            action=change_state("SetLanguage", main_menu=self.main_menu),
            font_size=self.font_type.small,
        )

        _native_w, _native_h = 256, 144
        _current_w = self.client.config.resolution[0]
        _current_scale = max(1, min(5, _current_w // _native_w))
        _size_default = _current_scale - 1

        def on_change_screen_size(value: Any, scale: int) -> None:
            new_w = _native_w * scale
            new_h = _native_h * scale
            self.client.config.update_attribute(
                "display", "resolution_x", new_w, save=False
            )
            self.client.config.update_attribute(
                "display", "resolution_y", new_h
            )

        screen_sizes: list[tuple[Any, ...]] = [
            (f"{_native_w * i}x{_native_h * i}", i) for i in range(1, 6)
        ]
        menu.add.selector(
            title=T.translate("menu_screen_size").upper(),
            items=screen_sizes,
            selector_id="screen_size",
            default=_size_default,
            style="fancy",
            onchange=on_change_screen_size,
            font_size=self.font_type.small,
        )


        if not self.main_menu:

            def toggle_mute() -> None:
                self.client.current_music.toggle_mute()

                # Persist logical volume (0 if muted, user volume otherwise)
                new_vol = self.client.current_music.get_volume()
                self.client.config.update_attribute(
                    "gameplay", "music_volume", new_vol
                )

            is_muted = self.client.current_music.muted
            title = (
                T.translate("menu_unmute_music")
                if is_muted
                else T.translate("menu_mute_music")
            )

            menu.add.button(
                title=title.upper(),
                action=toggle_mute,
                font_size=self.font_type.small,
            )

            _music = self.client.config.music_volume
            default_music = int(float(_music) * 100)
            _sound = self.client.config.sound_volume
            default_sound = int(float(_sound) * 100)

            unit = self.client.config.unit_measure
            _unit = 0 if str(unit) == "metric" else 1

            hemi = self.client.config.hemisphere
            _hemi = 0 if str(hemi) == "northern" else 1

            music = menu.add.range_slider(
                title=T.translate("menu_music_volume").upper(),
                default=default_music,
                range_values=(0, 100),
                increment=10,
                rangeslider_id="menu_music_volume",
                value_format=lambda x: str(int(x)),
                font_size=self.font_type.small,
            )
            sound = menu.add.range_slider(
                title=T.translate("menu_sound_volume").upper(),
                default=default_sound,
                range_values=(0, 100),
                increment=10,
                rangeslider_id="menu_sound_volume",
                value_format=lambda x: str(int(x)),
                font_size=self.font_type.small,
            )

            def on_change_music(val: int) -> None:
                """
                Updates the value.
                """
                volume = round(val / 100, 1)
                self.client.config.update_attribute(
                    "gameplay", "music_volume", volume
                )
                self.client.current_music.set_volume(volume)

            def on_change_sound(val: int) -> None:
                """
                Updates the value.
                """
                volume = round(val / 100, 1)
                self.client.config.update_attribute(
                    "gameplay", "sound_volume", volume
                )
                sound = self.menu.get_sound()
                sound.set_sound_volume(SOUND_TYPE_WIDGET_SELECTION, volume)

            music.set_onchange(on_change_music)
            sound.set_onchange(on_change_sound)

            def on_change_units(value: Any, label: str) -> None:
                """
                Updates the value.
                """
                self.client.config.update_attribute(
                    "gameplay", "unit_measure", label.lower()
                )

            metric = T.translate("menu_units_metric")
            imperial = T.translate("menu_units_imperial")
            units: list[tuple[Any, ...]] = []
            units = [(metric, metric), (imperial, imperial)]
            menu.add.selector(
                title=T.translate("menu_units").upper(),
                items=units,
                selector_id="unit",
                default=_unit,
                style="fancy",
                onchange=on_change_units,
                font_size=self.font_type.small,
            )

            def on_change_hemisphere(value: Any, label: str) -> None:
                """
                Updates the value.
                """
                self.client.config.update_attribute(
                    "gameplay", "hemisphere", label.lower()
                )

            north_hemi = T.translate("menu_hemisphere_north")
            south_hemi = T.translate("menu_hemisphere_south")
            hemispheres: list[tuple[Any, ...]] = []
            hemispheres = [(north_hemi, north_hemi), (south_hemi, south_hemi)]
            menu.add.selector(
                title=T.translate("menu_hemisphere").upper(),
                items=hemispheres,
                selector_id="hemisphere",
                default=_hemi,
                style="fancy",
                onchange=on_change_hemisphere,
                font_size=self.font_type.small,
            )

    def reload_controls(self) -> None:
        self.client.config.input.reload_input_map()
        keyboard = self.client.input_manager.core_devices.keyboard
        if keyboard is not None:
            keyboard.reload_mapping(
                self.client.config.input.keyboard_button_map
            )

    def process_event(self, event: PlayerInput) -> PlayerInput | None:
        if event.button in (buttons.BACK, buttons.B):
            self.reload_controls()
            if not self.main_menu:
                self.client.remove_state_by_name("ControlState")

        return super().process_event(event)
