# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum, auto
from functools import partial
from typing import TYPE_CHECKING

from tuxemon.core.core_effect import ItemEffectResult
from tuxemon.item.item import Item
from tuxemon.locale.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.session import Session
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.tools import open_dialog, show_result_as_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


class ItemAction(Enum):
    USE = auto()
    CANCEL = auto()
    INSPECT = auto()


def noop_action() -> None:
    """A no-operation function for unhandled actions."""


class ItemController:
    def __init__(self, session: Session, item: Item, character: NPC) -> None:
        self.session = session
        self.item = item
        self.char = character

    def _show_item_result(self, result: ItemEffectResult) -> None:
        if (
            self.item.behaviors.show_dialog_on_failure and not result.success
        ) or (self.item.behaviors.show_dialog_on_success and result.success):
            show_result_as_dialog(self.session, self.item, result.success)

    def get_basic_action(self, key: str) -> Callable[[], None]:
        try:
            action_enum = ItemAction[key.upper()]
        except KeyError:
            logger.warning(
                f"Unknown item menu action key '{key}' for item '{self.item.slug}'"
            )
            return noop_action

        if action_enum == ItemAction.USE:

            def action_use() -> None:
                self.session.client.remove_state_by_name("ChoiceState")
                if self.item.behaviors.requires_monster_menu:
                    monster_menu = MonsterMenuState(
                        self.session.client, self.char.monsters
                    )
                    self.session.client.push_state(monster_menu)
                    monster_menu = MonsterMenuState(
                        self.session.client,
                        self.char.monsters,
                        on_selection=self.get_monster_targeted_action(key),
                        is_valid_entry=partial(
                            self.item.validate_monster, self.session
                        ),
                    )
                    self.session.client.push_state(monster_menu)
                else:
                    result = self.item.use(self.session, self.char, None)
                    self.char.last_used_item_slug = self.item.slug
                    self.session.client.remove_state_by_name("ItemMenuState")
                    self.session.client.remove_state_by_name("WorldMenuState")
                    self._show_item_result(result)

            return action_use

        elif action_enum == ItemAction.INSPECT:

            def action_inspect() -> None:
                self.session.client.remove_state_by_name("ChoiceState")
                open_dialog(
                    self.session.client,
                    [
                        f"Upon closer inspection, the {self.item.name} is: {self.item.description.lower()}"
                    ],
                )

            return action_inspect

        elif action_enum == ItemAction.CANCEL:
            return lambda: self.session.client.remove_state_by_name(
                "ChoiceState"
            )

        return noop_action

    def get_monster_targeted_action(
        self, key: str
    ) -> Callable[[MenuItem[Monster | None]], None]:
        def action(menu_item: MenuItem[Monster | None]) -> None:
            monster = menu_item.game_object
            if monster is None:
                return

            monster = menu_item.game_object
            result = self.item.use(self.session, self.char, monster)
            self.char.last_used_item_slug = self.item.slug
            self.session.client.remove_state_by_name("MonsterMenuState")
            self.session.client.remove_state_by_name("ItemMenuState")
            self.session.client.remove_state_by_name("WorldMenuState")
            self._show_item_result(result)

        return action

    def _default_cancel_option(self) -> ChoiceOption:
        return ChoiceOption(
            key="cancel",
            display_text=T.translate("item_confirm_cancel").upper(),
            action=lambda: self.session.client.remove_state_by_name(
                "ChoiceState"
            ),
        )

    def get_confirm_menu_options(self) -> MenuOptions:
        options: list[ChoiceOption] = []

        if self.item.menu_actions_data:
            for action_data in self.item.menu_actions_data:
                key = action_data.key
                display_text = T.translate(action_data.display_text)
                action_func = self.get_basic_action(key)
                options.append(
                    ChoiceOption(
                        key=key,
                        display_text=display_text,
                        action=action_func,
                    )
                )
        else:
            if self.item.confirm_text:
                options.append(
                    ChoiceOption(
                        key="use",
                        display_text=self.item.confirm_text.upper(),
                        action=self.get_basic_action("use"),
                    )
                )
            if self.item.cancel_text:
                options.append(
                    ChoiceOption(
                        key="cancel",
                        display_text=self.item.cancel_text.upper(),
                        action=self.get_basic_action("cancel"),
                    )
                )

        if not any(
            opt.key.strip().lower() in ("cancel", "back", "close")
            for opt in options
        ):
            options.append(self._default_cancel_option())

        return MenuOptions(options)
