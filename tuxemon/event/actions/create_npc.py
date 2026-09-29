# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

from tuxemon.database.runtime import db
from tuxemon.db import (
    DialogueContent,
    DialogueProfile,
    NpcModel,
)
from tuxemon.entity.appearance import RuntimeAppearance
from tuxemon.entity.behavior.registry import create_behavior
from tuxemon.entity.npc import NPC
from tuxemon.event.eventaction import EventAction
from tuxemon.item.item import Item
from tuxemon.monster.monster import Monster

if TYPE_CHECKING:
    from tuxemon.db import PartyMemberModel
    from tuxemon.game_variables import GameVariablesManager
    from tuxemon.session import Session

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
    behavior: str | None = None

    def start(self, session: Session) -> None:
        slug = self.npc_slug

        if session.client.npc_manager.npc_exists(slug):
            self.stop()
            return

        npc = NPC.create(session, slug)
        session.client.npc_manager.place_npc_on_map(
            npc, slug, self.tile_pos_x, self.tile_pos_y
        )

        if self.behavior:
            npc.behavior_policy = create_behavior(self.behavior)
        npc_details = load_party(slug)

        npc.template = npc_details.template
        npc.combat = npc_details.combat
        npc.audio = npc_details.audio

        npc.appearance_manager.state = RuntimeAppearance.from_template(
            npc.template
        )
        npc.sprite_controller.update_appearance(npc.appearance_manager.state)

        variable_manager = session.player.variable_manager

        if npc_details.monsters:
            load_party_monsters(npc, npc_details, variable_manager)

        if npc_details.items:
            load_party_items(npc, npc_details, variable_manager)

        npc.dialogue = merge_dialogue(npc_details.speech.profile, None)


def load_party(slug: str) -> NpcModel:
    NpcModel.load_cache(db)
    cache = NpcModel.get_cache()

    try:
        return cache[slug]
    except KeyError:
        # fallback to direct lookup (should not happen if DB is consistent)
        npc = NpcModel.lookup(slug, db)
        cache[slug] = npc
        return npc


def load_party_monsters(
    npc: NPC, party: NpcModel, variable_manager: GameVariablesManager
) -> None:
    """Loads the NPC's party monsters from the database."""
    npc.party.clear_party()
    for npc_monster in party.monsters:
        if npc_monster.variables and variable_manager.check_conditions(
            npc_monster.variables
        ):
            monster = party_monster(npc_monster)
            npc.party.insert_monster_to_party(monster, len(npc.monsters))


def party_monster(npc_monster: PartyMemberModel) -> Monster:
    """Creates a new monster object from the database details."""
    monster = Monster.spawn_base(npc_monster.slug, npc_monster.level)
    monster.money_modifier = npc_monster.money_mod
    monster.set_experience_modifier(npc_monster.exp_req_mod)
    monster.gender = npc_monster.gender
    return monster


def load_party_items(
    npc: NPC, bag: NpcModel, variable_manager: GameVariablesManager
) -> None:
    """Loads the NPC's items from the database."""
    npc.bag.clear_items()
    for npc_item in bag.items:
        if npc_item.variables and variable_manager.check_conditions(
            npc_item.variables
        ):
            item = Item.create(npc_item.slug)
            npc.bag.add_item(item, npc_item.quantity)


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


def merge_dialogue(
    source: DialogueProfile | None,
    fallback: DialogueProfile | None = None,
) -> DialogueProfile:
    """
    Merges a source DialogueProfile with a fallback.

    Dialogue fields from the source take precedence.
    Location-based overrides from both models are merged.
    """
    source = source or DialogueProfile(
        default=DialogueContent(
            greeting=None,
            idle=None,
            farewell=None,
            pre_battle=None,
            post_battle_win=None,
            post_battle_lose=None,
            post_battle_draw=None,
        )
    )
    fallback = fallback or DialogueProfile(
        default=DialogueContent(
            greeting=None,
            idle=None,
            farewell=None,
            pre_battle=None,
            post_battle_win=None,
            post_battle_lose=None,
            post_battle_draw=None,
        )
    )

    # Create the merged default DialogueContent
    merged_default_content_dict = fallback.default.model_dump(
        exclude_none=True
    )
    merged_default_content_dict.update(
        source.default.model_dump(exclude_none=True)
    )
    merged_default = DialogueContent.model_validate(
        merged_default_content_dict
    )

    # Merge the location-based overrides
    merged_location_based = {
        **fallback.location_based,
        **source.location_based,
    }

    # For any shared locations, we need to perform a deeper merge
    for location, source_content in source.location_based.items():
        if location in fallback.location_based:
            fallback_content = fallback.location_based[location]
            merged_content_dict = fallback_content.model_dump(
                exclude_none=True
            )
            merged_content_dict.update(
                source_content.model_dump(exclude_none=True)
            )
            merged_location_based[location] = DialogueContent.model_validate(
                merged_content_dict
            )

    return DialogueProfile(
        default=merged_default,
        location_based=merged_location_based,
    )
