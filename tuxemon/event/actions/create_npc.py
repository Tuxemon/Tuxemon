# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Optional, final

from tuxemon.db import NpcModel, PartyMemberModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CreateNpcAction(EventAction):
    """
    Create an NPC object and adds it to the game's current list of NPC's.

    Script usage:
        .. code-block::

            create_npc <npc_slug>,<tile_pos_x>,<tile_pos_y>[,<behavior>]

    Script parameters:
        npc_slug: NPC slug to look up in the NPC database.
        tile_pos_x: X position to place the NPC on.
        tile_pos_y: Y position to place the NPC on.
        behavior: Behavior of the NPC (e.g. "wander"). Unused for now.

    """

    name = "create_npc"
    npc_slug: str
    tile_pos_x: int
    tile_pos_y: int
    behavior: Optional[str] = None

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)

        slug = self.npc_slug

        for element in world.npcs:
            if element.slug == slug:
                logger.error(
                    f"'{slug}' already exists on the map. Skipping creation."
                )
                return

        npc = NPC(slug, world=world)
        client = self.session.client.event_engine
        client.execute_action(
            "char_position", [slug, self.tile_pos_x, self.tile_pos_y], True
        )
        npc.behavior = self.behavior
        npc_details = load_party(slug)
        npc.template = npc_details.template
        npc.forfeit = npc_details.forfeit
        game_variables = self.session.player.game_variables
        if npc_details.monsters:
            load_party_monsters(npc, npc_details, game_variables)
        if npc_details.items:
            load_party_items(npc, npc_details, game_variables)
        npc.sprite_renderer._load_sprites()


lookup_cache: dict[str, NpcModel] = {}


def load_party(slug: str) -> NpcModel:
    if slug in lookup_cache:
        return lookup_cache[slug]
    else:
        npc_details = db.lookup(slug, "npc")
        lookup_cache[slug] = npc_details
        return npc_details


def load_party_monsters(
    npc: NPC, party: NpcModel, game_variables: dict[str, Any]
) -> None:
    """Loads the NPC's party monsters from the database."""
    npc.monsters = []
    for npc_monster in party.monsters:
        if npc_monster.variables and check_variables(
            npc_monster.variables, game_variables
        ):
            monster = party_monster(npc_monster)
            npc.add_monster(monster, len(npc.monsters))


def party_monster(npc_monster: PartyMemberModel) -> Monster:
    """Creates a new monster object from the database details."""
    monster = Monster()
    monster.load_from_db(npc_monster.slug)
    monster.money_modifier = npc_monster.money_mod
    monster.experience_modifier = npc_monster.exp_req_mod
    monster.set_level(npc_monster.level)
    monster.set_moves(npc_monster.level)
    monster.current_hp = monster.hp
    monster.gender = npc_monster.gender
    return monster


def load_party_items(
    npc: NPC, bag: NpcModel, game_variables: dict[str, Any]
) -> None:
    """Loads the NPC's items from the database."""
    npc.items = []
    for npc_item in bag.items:
        if npc_item.variables and check_variables(
            npc_item.variables, game_variables
        ):
            item = Item(save_data=npc_item.model_dump())
            item.quantity = npc_item.quantity
            npc.add_item(item)


def check_variables(
    npc_vars: Sequence[dict[str, str]], game_variables: dict[str, Any]
) -> bool:
    return all(
        all(
            key in game_variables and game_variables[key] == value
            for key, value in variable.items()
        )
        for variable in npc_vars
    )
