# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE_CONTACTS
from tuxemon.platform.const.sizes import UNKNOWN_MAP_SLUG
from tuxemon.tools import open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC

logger = logging.getLogger(__name__)

MIN_FREQ = 88.0
MAX_FREQ = 108.0
INITIAL_FREQ = 98.0
TUNING_TOLERANCE = 0.2


class Loader:
    _radio_map_lists: dict[str, Any] | None = None
    _radio_data: dict[str, Any] | None = None

    @classmethod
    def get_radio_map_lists(
        cls, filename: str = "radio_map_lists.yaml"
    ) -> dict[str, Any]:
        yaml_path = paths.mods_folder / filename
        if not cls._radio_map_lists:
            raw_data = load_yaml(yaml_path)
            if not isinstance(raw_data, dict):
                raise ValueError("Invalid YAML data for radio map lists")
            cls._radio_map_lists = raw_data
        return cls._radio_map_lists

    @classmethod
    def get_radio_data(
        cls, filename: str = "radio_data.yaml"
    ) -> dict[str, Any]:
        yaml_path = paths.mods_folder / filename
        if not cls._radio_data:
            raw_data = load_yaml(yaml_path)
            if not isinstance(raw_data, dict):
                raise ValueError("Invalid YAML data for radio station data")
            cls._radio_data = raw_data
        return cls._radio_data


RADIO_MAP_LISTS = Loader.get_radio_map_lists()
RADIO_DATA = Loader.get_radio_data()


def _check_conditions(
    radio_state: NuPhoneRadioBase, conditions: dict[str, Any]
) -> bool:
    """Checks if the required conditions (map_slugs and variables) are met."""
    required_map_slug = conditions.get("map_slugs")
    if required_map_slug:
        required_map_slug = (
            [required_map_slug]
            if not isinstance(required_map_slug, list)
            else required_map_slug
        )
        if radio_state.current_map not in required_map_slug:
            return False

    required_vars = conditions.get("variables")
    if required_vars:
        game_vars = radio_state.char.game_variables
        for var_name, expected_value in required_vars.items():
            if game_vars.get(var_name) != expected_value:
                return False
    return True


def _get_broadcast_content(
    radio_state: NuPhoneRadioBase, station_slug: str
) -> tuple[list[str], dict[str, Any] | None]:
    """Finds the correct dialogue and variables to set for a given station slug."""
    station_content = RADIO_DATA.get(station_slug, {})
    ULTIMATE_FALLBACK_DIALOGUE = ["radio_static_msgid"]

    default_broadcast = station_content.get(
        "default", {"dialogue": ULTIMATE_FALLBACK_DIALOGUE}
    )

    dialogue_msgids: list[str] = default_broadcast.get(
        "dialogue", ULTIMATE_FALLBACK_DIALOGUE
    )
    set_variables: dict[str, Any] | None = None

    conditional_broadcasts = station_content.get("conditional_broadcasts", [])

    for broadcast in conditional_broadcasts:
        conditions = broadcast.get("conditions", {})
        if _check_conditions(radio_state, conditions):
            dialogue_msgids = broadcast.get("dialogue", dialogue_msgids)
            set_variables = broadcast.get("set_variables")
            break

    return dialogue_msgids, set_variables


class NuPhoneRadioBase(PygameMenuState, ABC):
    name: ClassVar[str] = "NuPhoneRadioBase"

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.char = character
        if self.char.current_map:
            self.current_map = self.char.current_map.split(".")[0]
        else:
            self.current_map = UNKNOWN_MAP_SLUG

        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PHONE_CONTACTS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.reset_theme()

    def _apply_variable_changes(self, set_variables: dict[str, Any]) -> None:
        """Applies variables changes to the character's game variables (Shared)."""
        if set_variables:
            self.char.game_variables.update(set_variables)

    def _start_broadcast(self, station_slug: str) -> None:
        """Initiates the dialogue playback for the found station (Shared)."""

        dialogue_msgids, set_variables = _get_broadcast_content(
            self, station_slug
        )

        dialogue_text = [T.translate(msgid) for msgid in dialogue_msgids]
        on_dialog_complete = None
        if set_variables:
            on_dialog_complete = partial(
                self._apply_variable_changes, set_variables
            )

        open_dialog(
            self.client,
            dialogue_text,
            on_complete=on_dialog_complete,
            dialog_speed="max",
        )

    @abstractmethod
    def add_menu_items(self, menu: Menu) -> None:
        pass


class NuPhoneRadioMenu(NuPhoneRadioBase):
    name: ClassVar[str] = "NuPhoneRadioMenu"

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        super().__init__(client=client, character=character, **kwargs)
        self.add_menu_items(self.menu)

    def _start_radio_button(self, station_slug: str) -> None:
        """Starts the broadcast when a button is clicked."""
        self._start_broadcast(station_slug)

    def add_menu_items(self, menu: Menu) -> None:
        """Builds the menu with clickable station buttons based on map location."""
        available_stations = RADIO_MAP_LISTS.get(
            self.current_map, RADIO_MAP_LISTS.get("all_maps", [])
        )

        if not available_stations:
            menu.add.label(T.translate("radio_no_signal"), align=ALIGN_CENTER)
            return

        menu.add.label(
            title=T.translate("radio_station_list_header"),
            font_size=self.font_type.medium,
            align=ALIGN_CENTER,
        )

        menu.add.vertical_margin(10)

        for station_slug in available_stations:
            menu.add.button(
                title=T.translate(station_slug),
                action=partial(self._start_radio_button, station_slug),
                font_size=self.font_type.medium,
                align=ALIGN_CENTER,
            )
            menu.add.vertical_margin(15)

        menu.set_title(T.translate("app_radio")).center_content()


class NuPhoneRadioTuner(NuPhoneRadioBase):
    name: ClassVar[str] = "NuPhoneRadioTuner"
    current_station_slug: str = "station_scrambled_frequency"

    def __init__(
        self,
        client: BaseClient,
        character: NPC,
        frequency: float | None = None,
        **kwargs: Any,
    ) -> None:
        self.initial_freq = (
            frequency if frequency is not None else INITIAL_FREQ
        )
        self.selected_freq = self.initial_freq
        super().__init__(client=client, character=character, **kwargs)
        self.current_station_slug = "station_scrambled_frequency"
        self.add_menu_items(self.menu)

    def _play_selected_station(self) -> None:
        self._tune_radio(self.selected_freq, broadcast=False)
        best_match_slug = self._get_best_station_slug(self.selected_freq)
        signal_strength = self._get_signal_strength(self.selected_freq)

        if (
            signal_strength >= 80
            and best_match_slug != "station_scrambled_frequency"
        ):
            self._start_broadcast(best_match_slug)
            self.current_station_slug = best_match_slug
        else:
            self._start_broadcast("station_scrambled_frequency")
            self.current_station_slug = "station_scrambled_frequency"

    def _get_signal_strength(self, dial_value: float) -> int:
        min_diff = float("inf")

        map_specific = RADIO_MAP_LISTS.get(self.current_map, [])
        global_stations = RADIO_MAP_LISTS.get("all_maps", [])
        available_stations = set(map_specific + global_stations)

        for slug in available_stations:
            data = RADIO_DATA.get(slug)
            if not data or "frequency" not in data:
                continue

            station_freq = data["frequency"]
            diff = abs(dial_value - station_freq)
            if diff < min_diff:
                min_diff = diff

        return (
            max(0, int((1.0 - (min_diff / TUNING_TOLERANCE)) * 100))
            if min_diff != float("inf")
            else 0
        )

    def _signal_label(self, strength: int) -> str:
        if strength >= 80:
            return T.translate("signal_strong")
        elif strength >= 50:
            return T.translate("signal_moderate")
        elif strength > 0:
            return T.translate("signal_weak")
        else:
            return T.translate("signal_none")

    def _get_available_stations(self) -> set[str]:
        map_specific = RADIO_MAP_LISTS.get(self.current_map, [])
        global_stations = RADIO_MAP_LISTS.get("all_maps", [])
        return set(map_specific + global_stations)

    def _tune_radio(self, dial_value: float, broadcast: bool = True) -> None:
        self.selected_freq = dial_value
        signal_strength = self._get_signal_strength(dial_value)
        best_match_slug = self._get_best_station_slug(dial_value)

        station_label = self.menu.get_widget("station_label")
        if station_label:
            if best_match_slug == "station_scrambled_frequency":
                display_text = T.translate("radio_tuning_static")
            else:
                display_text = T.translate(
                    f"Tuning: {T.translate(best_match_slug)}"
                )
            station_label.set_title(display_text)

        if (
            broadcast
            and signal_strength >= 80
            and best_match_slug != self.current_station_slug
        ):
            self._start_broadcast(best_match_slug)
            self.current_station_slug = best_match_slug

        if hasattr(self, "signal_bar"):
            self.signal_bar.set_value(signal_strength)

    def _get_best_station_slug(self, dial_value: float) -> str:
        map_specific = RADIO_MAP_LISTS.get(self.current_map, [])
        global_stations = RADIO_MAP_LISTS.get("all_maps", [])
        available_stations = set(map_specific + global_stations)

        best_match_slug = "station_scrambled_frequency"
        min_diff = float("inf")

        for slug, data in RADIO_DATA.items():
            if slug not in available_stations:
                continue

            station_freq = data.get("frequency")
            if station_freq is None:
                continue

            diff = abs(dial_value - station_freq)
            if diff <= TUNING_TOLERANCE and diff < min_diff:
                min_diff = diff
                best_match_slug = slug

        return best_match_slug

    def add_menu_items(self, menu: Menu) -> None:
        """Builds the menu with the frequency tuner slider."""

        menu.add.label(
            title=T.translate("app_radio_tuner"),
            font_size=self.font_type.medium,
            align=ALIGN_CENTER,
        )
        menu.add.vertical_margin(10)

        menu.add.label(
            title=T.translate("radio_tuning_static"),
            font_size=self.font_type.medium,
            label_id="station_label",
            align=ALIGN_CENTER,
        )
        menu.add.vertical_margin(10)
        menu.add.label(
            title=T.translate("radio_tuner_hint"),
            font_size=self.font_type.small,
            align=ALIGN_CENTER,
        )
        menu.add.vertical_margin(10)
        menu.add.range_slider(
            title=T.translate("radio_tuner"),
            default=self.initial_freq,
            range_values=(MIN_FREQ, MAX_FREQ),
            increment=0.1,
            value_format=lambda x: f"{x:.1f} MHz",
            onchange=self._tune_radio,
            font_size=self.font_type.medium,
            align=ALIGN_CENTER,
        )
        menu.add.vertical_margin(10)
        self.signal_bar = menu.add.progress_bar(
            title=T.translate("radio_signal_strength"),
            default=0.0,
            range_values=(0, 100),
            progress_text=lambda val: f"{self._signal_label(val)} ({val}%)",
            font_size=self.font_type.small,
            align=ALIGN_CENTER,
        )
        self._tune_radio(self.initial_freq, broadcast=False)
        menu.add.vertical_margin(10)
        menu.add.button(
            title=T.translate("radio_play_button"),
            action=self._play_selected_station,
            font_size=self.font_type.medium,
            align=ALIGN_CENTER,
        )

        menu.set_title(T.translate("app_radio_tuner")).center_content()
