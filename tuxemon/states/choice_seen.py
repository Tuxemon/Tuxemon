# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from tuxemon.db import MonsterModel
from tuxemon.session import local_session
from tuxemon.states.choice_monster import ChoiceMonster, MenuMonsterConfig
from tuxemon.ui.menu_options import MenuOptions

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient


class ChoiceSeenMonster(ChoiceMonster):
    """
    Pick one of the species in the player's Tuxepedia.

    Like ChoiceMonster, but a name opens that species' Tuxepedia page as the
    player knows it. (ChoiceMonster marks the species caught and then wipes
    its entry, which suits a starter choice, not the player's own records.)
    """

    name: ClassVar[str] = "ChoiceSeenMonster"

    def __init__(
        self,
        client: BaseClient,
        menu: MenuOptions,
        escape_key_exits: bool = False,
        config: MenuMonsterConfig | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            client=client,
            menu=menu,
            escape_key_exits=escape_key_exits,
            config=config,
            **kwargs,
        )

    def open_journal(self, monster: MonsterModel) -> None:
        self.client.push_state(
            "JournalInfoState",
            character=local_session.player,
            monster=monster,
            source=self.name,
        )
