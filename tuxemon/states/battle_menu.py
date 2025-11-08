# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from functools import partial
from typing import ClassVar

from pygame_menu import locals
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import prepare
from tuxemon.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.player import Player
from tuxemon.session import local_session

DIFFICULTIES = ["beginner", "easy", "normal", "hard", "expert"]


class DifficultyBattleState(PygameMenuState):
    """
    A state that allows players to choose the difficulty level before entering the battle.
    """

    name: ClassVar[str] = "DifficultyBattleState"

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE
        super().__init__(height=height, width=width)

        self._build_menu()
        self.reset_theme()

    def _build_menu(self) -> None:
        """
        Constructs the difficulty selection menu with a title label and difficulty buttons.
        """
        title = T.translate("choose_difficulty")
        self.menu.add.label(
            title=title,
            font_size=self.font_type.big,
            align=locals.ALIGN_CENTER,
            underline=True,
        )

        for level in DIFFICULTIES:
            self.menu.add.button(
                title=T.translate(f"level_{level}"),
                action=partial(self.start_battle, level),
                button_id=f"diff_{level}",
                font_size=self.font_type.medium,
                selection_effect=HighlightSelection(),
                align=locals.ALIGN_CENTER,
            )

    def start_battle(self, difficulty: str) -> None:
        Player.create(local_session, slug=prepare.PLAYER_NPC)
        self.client.push_state(
            "WorldState", session=local_session, map_name=None
        )
        self.client.event_engine.execute_action(
            "set_variable", [f"difficulty:{difficulty}"]
        )
        self.client.event_engine.execute_action("load_yaml", ["battle_menu"])
