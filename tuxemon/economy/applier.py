# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tuxemon.db import Acquisition, EconomyItemModel, EconomyMonsterModel
from tuxemon.economy.economy import Economy
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.economy.shop_manager import ShopManager
    from tuxemon.entity.npc import NPC
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
    Applies an Economy's definitions to a character (NPC),
    creating items/monsters and populating shop inventories
    using ShopManager for persistent stock tracking.
    """

    def _process_economy_entity(
        self,
        economy: Economy,
        entity: NPC,
        eco_model: EconomyItemModel | EconomyMonsterModel,
        shop_manager: ShopManager,
    ) -> Item | Monster | None:
        """Process a single item or monster model and return the created entity, or None."""

        entity_name = eco_model.slug
        label = shop_manager.get_full_label(economy.model.slug, entity_name)
        is_item = isinstance(eco_model, EconomyItemModel)
        entity_type = "Item" if is_item else "Monster"

        default_quantity = (
            eco_model.inventory if is_item else (eco_model.inventory or 1)
        )
        quantity = shop_manager.get_or_set_default(label, default_quantity)

        if (
            eco_model.variables
            and not entity.variable_manager.check_conditions(
                eco_model.variables
            )
        ):
            logger.debug(
                f"Skipping {entity_type} '{entity_name}' (variables mismatch)"
            )
            return None

        try:
            if is_item:
                item_instance = Item.create(entity_name)
                item_instance.set_quantity(quantity)
                return item_instance
            else:
                assert isinstance(eco_model, EconomyMonsterModel)
                monster_instance = Monster.spawn_base(
                    entity_name, eco_model.level
                )
                monster_instance.set_acquisition(Acquisition.PURCHASED)
                return monster_instance
        except Exception as e:
            logger.error(
                f"[{economy.model.slug}] Could not create {entity_type} '{entity_name}': {type(e).__name__}: {e}"
            )
            return None

    def get_available_items(
        self,
        session: Session,
        economy: Economy,
        shop_manager: ShopManager,
    ) -> list[Item]:
        """Return the list of available items for the given session and economy."""
        player = session.player
        shop_items: list[Item] = []
        for eco_item_model in economy.model.items:
            item = self._process_economy_entity(
                economy, player, eco_item_model, shop_manager
            )
            if isinstance(item, Item):
                shop_items.append(item)
        return shop_items

    def get_available_monsters(
        self,
        session: Session,
        economy: Economy,
        shop_manager: ShopManager,
    ) -> list[Monster]:
        """Return the list of available monsters for the given session and economy."""
        player = session.player
        shop_monsters: list[Monster] = []
        for eco_monster_model in economy.model.monsters:
            monster = self._process_economy_entity(
                economy, player, eco_monster_model, shop_manager
            )
            if isinstance(monster, Monster):
                shop_monsters.append(monster)
        return shop_monsters

    def apply_economy_to_character(
        self,
        session: Session,
        economy: Economy,
        character: NPC,
        shop_manager: ShopManager,
    ) -> None:
        """
        Apply economy-defined items and monsters to a character's shop inventory.
        Uses ShopManager for persistent stock.
        """
        items = self.get_available_items(session, economy, shop_manager)
        monsters = self.get_available_monsters(session, economy, shop_manager)
        character.shop_inventory = ShopInventory(
            items=items, monsters=monsters
        )
        logger.info(
            f"Shop inventory set for '{character.slug}' with {len(items)} items and {len(monsters)} monsters."
        )

    def filter_items(
        self,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
        shop_manager: ShopManager,
    ) -> list[Item]:
        if buyer.is_player:
            raw_inventory = (
                seller.shop_inventory.items if seller.shop_inventory else []
            )
            inventory = [
                item
                for item in raw_inventory
                if shop_manager.is_available(
                    f"{economy.model.slug}:{item.slug}"
                )
            ]
        else:
            inventory = [
                item for item in seller.items if item.behaviors.resellable
            ]

        return sorted(inventory, key=lambda x: x.name)

    def filter_monsters(
        self,
        buyer: NPC,
        seller: NPC,
        economy: Economy,
        shop_manager: ShopManager,
    ) -> list[Monster]:
        if buyer.is_player:
            raw_inventory = (
                seller.shop_inventory.monsters if seller.shop_inventory else []
            )
            inventory = [
                monster
                for monster in raw_inventory
                if shop_manager.is_available(
                    f"{economy.model.slug}:{monster.slug}"
                )
            ]
        else:
            inventory = list(seller.party.monsters)

        return sorted(inventory, key=lambda x: x.name)
