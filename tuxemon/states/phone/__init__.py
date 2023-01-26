# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Callable, Sequence, Tuple

from tuxemon.locale import T, replace_text
from tuxemon.menu.menu import Menu, PopUpMenu
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


MenuGameObj = Callable[[], object]


def add_menu_items(
    state: Menu[MenuGameObj],
    items: Sequence[Tuple[str, MenuGameObj]],
) -> None:
    for key, callback in items:
        label = T.translate(key).upper()

        state.build_item(label, callback)


def not_implemented_dialog() -> None:
    open_dialog(local_session, [T.translate("not_implemented")])


class NuPhone(PopUpMenu[MenuGameObj]):
    """The state Phone."""

    shrink_to_items = True

    def __init__(self) -> None:
        super().__init__()

        def bank() -> None:
            self.client.pop_state()
            types = self.client.map_type
            if types == "town" or types == "center" or types == "shop":
                template = T.translate("player_wallet")
                message = replace_text(local_session, template)
                open_dialog(local_session, [message])
            else:
                template = T.translate("no_signal_phone")
                open_dialog(local_session, [template])

        menu_items_map = [("menu_bank", bank)]

        add_menu_items(self, tuple(menu_items_map))
