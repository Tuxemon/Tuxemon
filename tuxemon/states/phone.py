# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.item.item import Item
from tuxemon.locale.locale import T
from tuxemon.map.manager import MAP_TYPES, MapType
from tuxemon.menu.menu import PygameMenuState
from tuxemon.platform.const.graphics import BG_PHONE
from tuxemon.tools import fix_measure, open_dialog

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC


class NuPhone(PygameMenuState):
    """Menu for Nu Phone."""

    name: ClassVar[str] = "NuPhone"

    def __init__(
        self, client: BaseClient, character: NPC, **kwargs: Any
    ) -> None:
        width, height = client.context.resolution
        self.char = character

        self.menu_apps: list[Item] = []
        for itm in self.char.items:
            if itm.dynamic_menu and itm.dynamic_menu.menu_type == "phone":
                self.menu_apps.append(itm)

        columns = 4
        rows = math.ceil(len(self.menu_apps) / columns) * 3

        super().__init__(
            client=client,
            height=height,
            width=width,
            columns=columns,
            rows=rows,
            **kwargs,
        )

        theme = self._setup_theme(BG_PHONE)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        theme.title = True
        self._menu_config["theme"] = theme

        self.add_menu_items(self.menu, self.menu_apps)
        self.reset_theme()

    def _get_app_callback(self, item: Item) -> Callable[[], Any]:
        """
        Returns the appropriate callback for a dynamic menu entry,
        handling conditional logic based on the item and game state.
        """
        dm = item.dynamic_menu
        if not dm:
            return lambda: None

        state_name = dm.state

        def _no_trackers() -> None:
            open_dialog(
                self.client,
                [T.translate("nu_map_missing")],
                dialog_speed="max",
            )

        def _no_signal() -> None:
            open_dialog(
                self.client, [T.translate("no_signal")], dialog_speed="max"
            )

        if state_name == "NuPhoneBanking":
            # Banking app requires a network signal
            network = self._get_network_map_types()
            if self.client.map_manager.map_type not in network:
                return _no_signal

        if state_name == "NuPhoneMap":
            # Map app requires a tracker
            if not self.char.tracker.locations:
                return _no_trackers

        return partial(self.client.push_state, state_name, character=self.char)

    def add_menu_items(
        self,
        menu: Menu,
        items: Sequence[Item],
    ) -> None:
        """Dynamically adds app items to the phone menu."""

        def _uninstall(itm: Item) -> None:
            open_dialog(
                self.client, [T.translate("uninstall_app")], dialog_speed="max"
            )

        column_width = fix_measure(menu._width, 0.25)
        menu._column_max_width = [column_width] * 4
        network = self._get_network_map_types()

        if self.client.map_manager.map_type in network:
            desc = T.translate("omnichannel_mobile")
        else:
            desc = T.translate("no_signal")

        menu.set_title(desc).center_content()

        for item in items:
            dm = item.dynamic_menu
            if dm:
                label = T.translate(dm.label_key).upper()

                change = self._get_app_callback(item)

                new_image = self._create_image(item.sprite)
                new_image.scale(self.factor, self.factor)

                # App image (banner)
                menu.add.banner(
                    new_image,
                    change,
                    selection_effect=HighlightSelection(),
                )

                # App name (button with uninstall action)
                menu.add.button(
                    label,
                    action=partial(_uninstall, item),
                    font_size=self.font_type.smaller,
                )

                # App description
                menu.add.label(
                    item.description,
                    font_size=self.font_type.smaller,
                    wordwrap=True,
                )

    def _get_network_map_types(self) -> set[MapType]:
        return {
            MAP_TYPES[name]
            for name in {"town", "clinic", "shop"}
            if name in MAP_TYPES
        }
