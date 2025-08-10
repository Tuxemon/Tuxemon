# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tuxemon.db import Acquisition
from tuxemon.economy.economy import Economy
from tuxemon.item.item import Item
from tuxemon.monster import Monster

if TYPE_CHECKING:
    from tuxemon.npc import NPC
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class ShopInventory:
    items: list[Item] = field(default_factory=list)
    monsters: list[Monster] = field(default_factory=list)

    def has_item(self, slug: str) -> bool:
        return any(item.slug == slug for item in self.items)

    def has_monster(self, slug: str) -> bool:
        return any(monster.slug == slug for monster in self.monsters)


class EconomyApplier:
    """
    Manages the application of an Economy's definitions to a character (e.g., NPC),
    creating actual game entities (Items, Monsters) and populating their inventories
    based on economy data and character game variables.
    """

    def apply_economy_to_character(
        self, session: Session, economy: Economy, character: NPC
    ) -> None:
        """
        Applies economy-defined items and monsters to a character, populating a separate
        shop inventory based on the player's game variables and availability conditions.
        """
        player = session.player
        shop_items = []
        shop_monsters = []

        # Process items
        for eco_item_model in economy.model.items:
            label = f"{economy.model.slug}:{eco_item_model.name}"

            if label not in player.game_variables:
                initial_quantity = economy.lookup_item_field(
                    eco_item_model.name, "inventory"
                )
                player.game_variables[label] = initial_quantity

            if eco_item_model.variables and not economy.variable(
                eco_item_model.variables, player
            ):
                logger.debug(f"Skipping item '{eco_item_model.name}'")
                continue

            try:
                item_instance = Item.create(eco_item_model.name)
                item_instance.set_quantity(int(player.game_variables[label]))
                shop_items.append(item_instance)
            except Exception as e:
                logger.error(
                    f"Could not create Item '{eco_item_model.name}': {e}"
                )

        # Process monsters
        for eco_monster_model in economy.model.monsters:
            label = f"{economy.model.slug}:{eco_monster_model.name}"

            if label not in player.game_variables:
                default = (
                    economy.get_monster_field(
                        eco_monster_model.name, "inventory"
                    )
                    or 1
                )
                player.game_variables[label] = default

            if eco_monster_model.variables and not economy.variable(
                eco_monster_model.variables, player
            ):
                logger.debug(f"Skipping monster '{eco_monster_model.name}'")
                continue

            try:
                monster = Monster.spawn_base(
                    eco_monster_model.name, eco_monster_model.level
                )
                monster.set_acquisition(Acquisition.PURCHASED)
                shop_monsters.append(monster)
            except Exception as e:
                logger.error(
                    f"Could not create Monster '{eco_monster_model.name}': {e}"
                )

        character.shop_inventory = ShopInventory(
            items=shop_items, monsters=shop_monsters
        )
        logger.info(
            f"Shop inventory set for '{character.slug}' with {len(shop_items)} items and {len(shop_monsters)} monsters."
        )
