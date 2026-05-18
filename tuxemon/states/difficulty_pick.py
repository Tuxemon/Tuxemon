# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient

DIFFICULTIES = ["beginner", "easy", "normal", "hard", "expert"]


class DifficultyPickState(PygameMenuState):
    """Generic difficulty selection state."""

    name: ClassVar[str] = "DifficultyPickState"

    def __init__(
        self,
        client: BaseClient,
        on_pick: Callable[[str], None],
        difficulties: list[str] = DIFFICULTIES,
        **kwargs: Any,
    ) -> None:
        width, height = client.context.resolution
        super().__init__(client=client, height=height, width=width, **kwargs)

        self.on_pick = on_pick
        self.difficulties = difficulties
        self._build_menu()
        self.reset_theme()

    def _build_menu(self) -> None:
        title = T.translate("choose_difficulty")
        self.menu.add.label(
            title=title,
            font_size=self.font_type.big,
            align=ALIGN_CENTER,
            underline=True,
        )

        for level in self.difficulties:
            self.menu.add.button(
                title=T.translate(f"level_{level}"),
                action=partial(self._handle_pick, level),
                button_id=f"diff_{level}",
                font_size=self.font_type.medium,
                selection_effect=HighlightSelection(),
                align=ALIGN_CENTER,
            )

    def _handle_pick(self, difficulty: str) -> None:
        self.on_pick(difficulty)
