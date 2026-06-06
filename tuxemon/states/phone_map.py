# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE_MAP
from tuxemon.tools import fix_measure

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC


logger = logging.getLogger(__name__)


@dataclass
class NuPhoneMapConfig:
    map_path: str
    map_data: list[tuple[float, float, str]]


class Loader:
    _config_nuphone_map: NuPhoneMapConfig | None = None

    @classmethod
    def get_config_nuphone_map(cls, filename: str) -> NuPhoneMapConfig:
        yaml_path = paths.mods_folder / filename
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


class NuPhoneMap(PygameMenuState):
    """
    If there is no variable, then it'll be shown the Spyder map.

    where location is the msgid of the location (PO), x and y are coordinates

    If the player is in Cotton Town, then Cotton Town will be underlined and not
    selectable.

    If there are no trackers (locations), then it'll be not possible to consult
    the app. It'll appear a pop up with: "GPS tracker not updating."
    """

    name: ClassVar[str] = "NuPhoneMap"

    def add_menu_items(
        self,
        menu: Menu,
    ) -> None:
        new_image = self._create_image(data.map_path)
        new_image.scale(self.factor, self.factor)
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
                        player_icon = self._create_image("gfx/ui/menu/player.png")
                        player_icon.scale(self.factor, self.factor)
                        menu.add.image(player_icon.copy(), float=True).translate(
                            fix_measure(menu._width, x),
                            fix_measure(menu._height, y),
                        )

                    lab: Any = menu.add.label(
                        title=T.translate(key),
                        selectable=selectable,
                        float=True,
                        underline=underline,
                        font_size=self.font_type.small,
                    )
                    lab.translate(
                        fix_measure(menu._width, x),
                        fix_measure(menu._height, y),
                    )

        menu.set_title(title=T.translate("app_map")).center_content()

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        self.char = character
        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_PHONE_MAP)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu)
        self.reset_theme()
