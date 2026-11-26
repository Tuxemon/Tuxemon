# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import (
    ALIGN_CENTER,
    ORIENTATION_VERTICAL,
    POSITION_EAST,
)

from tuxemon.menu.menu import PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.menu.transitions import PopInClamped
from tuxemon.ui.menu_options import MenuOptions

if TYPE_CHECKING:
    from pygame_menu import Menu
    from pygame_menu.widgets import Widget

    from tuxemon.base_client import BaseClient


@dataclass
class MenuStateConfig:
    max_elements: int = 13
    max_height_percentage: float = 0.8


class ChoiceState(PygameMenuState):
    """
    Game state with a graphic box and some text in it.

    Pressing the action button:
    * if text is being displayed, will cause text speed to go max
    * when text is displayed completely, then will show the next message
    * if there are no more messages, then the dialog will close
    """

    name: ClassVar[str] = "ChoiceState"

    def __init__(
        self,
        client: BaseClient,
        menu: MenuOptions,
        escape_key_exits: bool = False,
        config: MenuStateConfig | None = None,
        title: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.config = config or MenuStateConfig()

        super().__init__(
            client=client,
            transition=PopInClamped(
                max_height_percentage=self.config.max_height_percentage
            ),
            **kwargs,
        )

        theme = get_theme(self.client.context.scaling).copy()

        # The title is a row too: a list that is one row over the limit
        # because of it must scroll like any other long list (without this
        # the last rows of a 13-option list with a title were cut off and
        # could not be scrolled to).
        if len(menu.options) + (1 if title else 0) > self.config.max_elements:
            theme.scrollarea_position = POSITION_EAST

        self._menu_config["theme"] = theme

        self.title = title
        if title:
            # A centred, underlined header. Labels cannot be selected: the
            # cursor starts on the first option.
            self.menu.add.label(title, align=ALIGN_CENTER, underline=True)
            self.menu.add.vertical_margin(self.font_type.smaller)

        for index, option in enumerate(menu.get_menu()):
            button = self.menu.add.button(
                option.display_text,
                option.action,
                font_size=self.font_type.medium,
            )
            if title and index == 0:
                button.set_onselect(self._show_title)

        self.escape_key_exits = escape_key_exits

    @staticmethod
    def _show_title(selected: bool, widget: Widget, menu: Menu) -> None:
        """
        Scrolls a long list back to its top when the first option is selected.

        The list scrolls just far enough to show the selected option, and the
        title cannot be selected, so without this a title that has scrolled
        out of view would never come back.
        """
        if selected:
            menu.get_scrollarea().scroll_to(ORIENTATION_VERTICAL, 0)
