# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tuxemon.ai.ai import AI
from tuxemon.db import StatType

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class AIManager:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.active_ais: dict[Monster, AI] = {}

    def process_ai_turn(self, monster: Monster, character: NPC) -> None:
        """
        Processes a single AI monster's turn.
        Retrieves or creates the AI instance and tells it to take its turn.
        """
        if monster not in self.active_ais:
            logger.debug(f"New AI instance for monster: {monster}")
            self.active_ais[monster] = AI(self.session, monster, character)

        ai_instance = self.active_ais[monster]
        logger.debug(f"AI turn for monster: {monster}")
        ai_instance.take_turn()

    def remove_ai(self, monster: Monster) -> None:
        """Removes the AI instance associated with the given monster."""
        if monster in self.active_ais:
            logger.debug(f"Removing AI for monster: {monster}")
            del self.active_ais[monster]

    def clear_ai(self) -> None:
        """Removes all tracked AI instances from the manager."""
        logger.debug("Clearing all AI instances.")
        self.active_ais.clear()

    def choose_replacement_monster(self, character: NPC) -> Monster | None:
        """
        AI logic to select a replacement monster to send out.

        This method uses the available monsters and applies AI strategy.
        """
        available_monsters = self.session.client.combat_session.get_bench(
            character
        )

        if not available_monsters:
            logger.debug(f"No available monsters for {character.name}")
            return None

        if len(available_monsters) == 1:
            logger.debug(
                f"Only one monster available for {character.name}: {available_monsters[0].name}"
            )
            return available_monsters[0]

        strategy = character.combat.switch_logic
        logger.debug(f"{character.name} strategy: {strategy}")

        # If no strategy, pick the next available monster in order
        if strategy is None:
            logger.debug(
                f"No strategy defined. Selecting first available monster: {available_monsters[0].name}"
            )
            return available_monsters[0]

        methods = {
            "lv_highest": ("level", max),
            "lv_lowest": ("level", min),
            "healthiest": ("current_hp", max),
            "weakest": ("current_hp", min),
            "oldest": ("steps", max),
            "newest": ("steps", min),
        }

        methods.update(
            {f"{stat.value}_max": (stat.value, max) for stat in StatType}
        )
        methods.update(
            {f"{stat.value}_min": (stat.value, min) for stat in StatType}
        )

        if strategy == "random":
            chosen = random.choice(available_monsters)
            logger.debug(f"Random strategy selected: {chosen.name}")
            return chosen

        if strategy in methods:
            attr, func = methods[strategy]
            chosen = func(available_monsters, key=lambda m: getattr(m, attr))
            logger.debug(
                f"Strategy '{strategy}' selected monster: {chosen.name} (based on {attr})"
            )
            return chosen

        logger.debug(
            f"Unrecognized strategy '{strategy}'. Defaulting to first available: {available_monsters[0].name}"
        )
        return available_monsters[0]
