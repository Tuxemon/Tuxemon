# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import pygame_menu
import yaml
from pygame_menu import locals

from tuxemon import prepare
from tuxemon.constants import paths
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState

if TYPE_CHECKING:
    from tuxemon.npc import NPC

MenuGameObj = Callable[[], Any]

logger = logging.getLogger(__name__)


@dataclass
class NuPhoneMapConfig:
    map_path: str
    map_data: list[tuple[float, float, str]]


def load_yaml(filepath: str) -> Any:
    try:
        with open(filepath) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


class Loader:
    _config_nuphone_map: Optional[NuPhoneMapConfig] = None

    @classmethod
    def get_config_nuphone_map(cls, filename: str) -> NuPhoneMapConfig:
        yaml_path = f"{paths.mods_folder}/{filename}"
        if not cls._config_nuphone_map:
            raw_data = load_yaml(yaml_path)
            if not isinstance(raw_data, dict):
                raise ValueError("Invalid YAML data")

            map_path = raw_data.get("map_path")
            map_data = raw_data.get("map_data")
            if not map_path or not map_data:
                raise ValueError("Missing required keys in YAML data")

            map_data = [(item[0], item[1], item[2]) for item in map_data]

            cls._config_nuphone_map = NuPhoneMapConfig(
                map_path=map_path,
                map_data=map_data,
            )
        return cls._config_nuphone_map


data = Loader.get_config_nuphone_map("nu_phone_map.yaml")


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


class NuPhoneMap(PygameMenuState):
    """
    If there is no variable, then it'll be shown the Spyder map.

    where location is the msgid of the location (PO), x and y are coordinates

    If the player is in Cotton Town, then Cotton Town will be underlined and not
    selectable.

    If there are no trackers (locations), then it'll be not possible to consult
    the app. It'll appear a pop up with: "GPS tracker not updating."
    """

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
    ) -> None:
        new_image = self._create_image(data.map_path)
        new_image.scale(prepare.SCALE, prepare.SCALE)
        menu.add.image(image_path=new_image.copy())
        underline = False
        selectable = True

        for key, value in self.char.tracker.locations.items():
            for map_data in data.map_data:
                if key == map_data[2]:
                    x = map_data[0]
                    y = map_data[1]
                    # player is here
                    if self.client.map_manager.map_slug == key:
                        underline = True
                        selectable = False

                    lab: Any = menu.add.label(
                        title=T.translate(key),
                        selectable=selectable,
                        float=True,
                        underline=underline,
                        font_size=self.font_size_small,
                    )
                    lab.translate(
                        fix_measure(menu._width, x),
                        fix_measure(menu._height, y),
                    )

        menu.set_title(title=T.translate("app_map")).center_content()

    def __init__(self, character: NPC) -> None:
        width, height = prepare.SCREEN_SIZE

        theme = self._setup_theme(prepare.BG_PHONE_MAP)
        theme.scrollarea_position = locals.POSITION_EAST
        theme.widget_alignment = locals.ALIGN_CENTER

        theme.title = True

        self.char = character

        super().__init__(
            height=height,
            width=width,
        )

        self.add_menu_items(self.menu)
        self.reset_theme()
