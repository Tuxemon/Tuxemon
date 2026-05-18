# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygame_menu.locals import ALIGN_CENTER, POSITION_EAST
from pygame_menu.menu import Menu

from tuxemon.locale.locale import T
from tuxemon.menu.menu import PygameMenuState
from tuxemon.monster.stats import compare_stats
from tuxemon.platform.const.graphics import BG_MISSIONS

if TYPE_CHECKING:
    from tuxemon.base_client import BaseClient
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster


class EvolutionState(PygameMenuState):
    """
    State that handles the evolution confirmation UI and decision.
    """

    name: ClassVar[str] = "EvolutionState"

    def __init__(
        self,
        client: BaseClient,
        monster: Monster,
        target: Monster,
        character: NPC,
        is_devolution: bool = False,
        **kwargs: Any,
    ) -> None:
        self.monster = monster
        self.target = target
        self.char = character
        self.is_devolution = is_devolution

        width, height = client.context.resolution

        super().__init__(client=client, height=height, width=width, **kwargs)

        theme = self._setup_theme(BG_MISSIONS)
        theme.scrollarea_position = POSITION_EAST
        theme.widget_alignment = ALIGN_CENTER
        self._menu_config["theme"] = theme
        self._build_menu(self.menu)
        self.reset_theme()

    def _build_menu(self, menu: Menu) -> None:
        old_name = self.monster.name.upper()
        new_name = self.target.name.upper()

        stat_changes = compare_stats(
            self.monster.base_stats, self.target.base_stats
        )

        msg_key = (
            "devolution_confirmation"
            if self.is_devolution
            else "evolution_confirmation"
        )
        ask_key = (
            "allow_devolution" if self.is_devolution else "allow_evolution"
        )

        menu.add.label(
            title=T.format(msg_key, {"name": old_name, "target": new_name}),
            font_size=self.font_type.small,
        )

        menu.add.vertical_margin(10)

        for stat_name, (old, new, delta) in stat_changes.items():
            sign = "+" if delta > 0 else ""
            text = f"{stat_name.upper()}: {old} → {new} ({sign}{delta})"
            menu.add.label(text, font_size=self.font_type.small)

        menu.add.vertical_margin(10)
        menu.add.label(
            title=T.translate(ask_key), font_size=self.font_type.small
        )
        menu.add.vertical_margin(10)

        menu.add.button(
            title=T.translate("yes").upper(),
            action=self._confirm,
            font_size=self.font_type.small,
        )
        menu.add.button(
            title=T.translate("no").upper(),
            action=self._deny,
            font_size=self.font_type.small,
        )

    def _confirm(self) -> None:
        """Player accepted the change."""
        if not self.is_devolution:
            registry = self.char.evolution_registry
            self.monster.evolution_handler.confirm_pending_evolution(
                registry, self.target.slug
            )

        self.monster.evolution_handler.evolve_monster(self.target)
        self.monster.waiting_to_evolve = False

        self.client.pop_state()
        self.client.push_state(
            "EvolutionTransition",
            original=self.monster.slug,
            evolved=self.target.slug,
            is_devolution=self.is_devolution,
        )

    def _deny(self) -> None:
        """Player refused the change."""
        if not self.is_devolution:
            registry = self.char.evolution_registry
            registry.log_missed(
                self.monster.instance_id, self.target.slug, self.monster.level
            )
            registry.clear_pending_slug(
                self.monster.instance_id, self.target.slug
            )

        self.monster.waiting_to_evolve = False
        self.client.pop_state()
