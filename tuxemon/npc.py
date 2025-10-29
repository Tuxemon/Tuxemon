# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.boxes import ItemBoxes, MonsterBoxes
from tuxemon.db import DialogueProfile, Direction, NpcModel, db
from tuxemon.entity import Entity
from tuxemon.entity_dir.bag import BagHandler
from tuxemon.entity_dir.battle import BattlesHandler
from tuxemon.entity_dir.party import PartyHandler
from tuxemon.entity_dir.path import PathController
from tuxemon.entity_dir.routing import RoutingPolicy
from tuxemon.game_variables import GameVariablesManager, PlayerVariablesManager
from tuxemon.locale import T
from tuxemon.map.map import proj
from tuxemon.map.map_view import SpriteController
from tuxemon.mission.controller import MissionController
from tuxemon.mission.manager import MissionManager
from tuxemon.money.controller import MoneyController
from tuxemon.monster import Monster
from tuxemon.monster_dir.evolution_registry import EvolutionRegistry
from tuxemon.relationship import (
    Relationships,
    decode_relationships,
    encode_relationships,
)
from tuxemon.save_state import NPCState
from tuxemon.step_tracker import StepTrackerManager, decode_steps, encode_steps
from tuxemon.teleporter import TeleportFaint
from tuxemon.tools import vector2_to_tile_pos
from tuxemon.tracker import TrackingData, decode_tracking, encode_tracking
from tuxemon.tuxepedia import Tuxepedia, decode_tuxepedia, encode_tuxepedia
from tuxemon.ui.cipher_processor import decode_cipher, encode_cipher

if TYPE_CHECKING:
    from tuxemon.economy.applier import ShopInventory
    from tuxemon.economy.economy import Economy
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


class NPC(Entity[NPCState]):
    """
    Class for humanoid type game objects, NPC, Players, etc.

    Currently, all movement is handled by a queue called "path".  This queue
    provides robust movement in a tile based environment.  It supports
    arbitrary length paths for directly setting a series of movements.

    Pathfinding is accomplished by setting the path directly.

    To move one tile, simply set a path of one item.
    """

    def __init__(
        self,
        npc_slug: str,
        *,
        session: Session,
    ) -> None:
        super().__init__(slug=npc_slug, session=session)

        # load initial data from the npc database
        npc_data = NpcModel.lookup(npc_slug, db)
        self.template = npc_data.template
        self.combat = npc_data.combat

        # This is the NPC's name to be used in dialog
        self.name = T.translate(self.slug)

        # general
        self.behavior: Optional[str] = "wander"  # not used for now
        self._variables = GameVariablesManager()
        self.battle_handler = BattlesHandler()
        # Tracks Tuxepedia (monster seen or caught)
        self.tuxepedia = Tuxepedia()
        self.relationships = Relationships()
        self.money_controller = MoneyController(self)
        # list of ways player can interact with the Npc
        self.interactions: Sequence[str] = []
        self.mission_controller = MissionController(self, MissionManager())
        self.economy: Optional[Economy] = None
        self.shop_inventory: Optional[ShopInventory] = None
        self.teleport_faint = TeleportFaint()
        self.tracker = TrackingData()
        self.step_tracker = StepTrackerManager()
        self.unlocked_letters: set[str] = set()
        # Variables for long-term item and monster storage
        # Keeping these separate so other code can safely
        # assume that all values are lists
        self.monster_boxes = MonsterBoxes()
        self.party = PartyHandler(monster_boxes=self.monster_boxes, owner=self)
        self.item_boxes = ItemBoxes()
        self.items = BagHandler(item_boxes=self.item_boxes)
        self.evolution_registry = EvolutionRegistry()
        self.steps: float = 0.0
        self.dialogue: Optional[DialogueProfile] = None
        self.sprite_controller = SpriteController(self)

        # PathController manages all path/pathfinding state & logic.
        self.path_controller = PathController(
            self,
            self.client.pathfinder,
            self.client.map_manager,
            self.client.npc_manager,
        )
        self.final_move_dest = [0, 0]

    @property
    def game_variables(self) -> PlayerVariablesManager:
        return self._variables.player

    @property
    def monsters(self) -> list[Monster]:
        """Returns the list of monsters in the party."""
        return self.party.monsters

    @property
    def path(self) -> list[tuple[int, int]]:
        """Returns the current movement path assigned to the NPC."""
        return self.path_controller.path

    @property
    def move_destination(self) -> Optional[tuple[int, int]]:
        """Returns the NPC's current movement destination tile, if any."""
        return self.path_controller.move_destination

    def get_state(self, session: Session) -> NPCState:
        """
        Prepares a dictionary of the npc to be saved to a file.

        Parameters:
            session: Game session.

        Returns:
            Dictionary containing all the information about the npc.
        """

        state: NPCState = {
            "current_map": session.client.get_map_name(),
            "facing": self.facing.value,
            "game_variables": self._variables.get_player_state(),
            "battles": self.battle_handler.encode_battle(),
            "tuxepedia": encode_tuxepedia(self.tuxepedia),
            "relationships": encode_relationships(self.relationships),
            "money": self.money_controller.save(),
            "items": self.items.encode_items(),
            "template": self.template.model_dump(),
            "missions": self.mission_controller.encode_missions(),
            "monsters": self.party.encode_party(),
            "player_slug": self.slug,
            "player_name": self.name,
            "player_steps": self.steps,
            "monster_boxes": self.monster_boxes.get_state(),
            "item_boxes": self.item_boxes.get_state(),
            "tile_pos": self.tile_pos,
            "teleport_faint": self.teleport_faint.to_dict(),
            "tracker": encode_tracking(self.tracker),
            "step_tracker": encode_steps(self.step_tracker),
            "unlocked_letters": encode_cipher(self.unlocked_letters),
            "evolution_registry": self.evolution_registry.encode_registry(),
            "routing_policy": self.party.routing_policy.to_dict(),
        }
        return state

    def set_state(self, session: Session, save_data: NPCState) -> None:
        """
        Recreates npc from saved data.

        Parameters:
            session: Game session.
            save_data: Data used to recreate the NPC.
        """
        self.set_facing(Direction(save_data.get("facing", "down")))
        self._variables.set_player_state(save_data["game_variables"])
        self.tuxepedia = decode_tuxepedia(save_data["tuxepedia"])
        self.relationships = decode_relationships(save_data["relationships"])
        self.battle_handler.decode_battle(save_data)
        self.items.decode_items(save_data)
        self.party.decode_party(save_data)
        self.mission_controller.decode_missions(save_data.get("missions"))
        self.slug = save_data["player_slug"]
        self.name = save_data["player_name"]
        self.steps = save_data["player_steps"]
        self.money_controller.load(save_data)
        self.unlocked_letters = decode_cipher(save_data)
        self.evolution_registry.decode_registry(
            save_data.get("evolution_registry", {})
        )
        self.monster_boxes.load(self, save_data)
        self.item_boxes.load(save_data)

        self.teleport_faint = TeleportFaint.from_dict(save_data)

        self.tracker = decode_tracking(save_data.get("tracker", {}))
        self.step_tracker = decode_steps(save_data.get("step_tracker", {}))
        self.party.routing_policy_name = RoutingPolicy.from_dict(save_data)

        _template = save_data["template"]
        self.template.slug = _template["slug"]
        self.template.sprite_name = _template["sprite_name"]
        self.template.combat_front = _template["combat_front"]
        self.sprite_controller.load_sprites(self.template)

    def pathfind(self, destination: tuple[int, int]) -> None:
        self.path_controller.start_path(destination)

    def set_path_and_start(self, path: list[tuple[int, int]]) -> None:
        self.path_controller.set_path_and_start(path)

    def cancel_path(self) -> None:
        self.path_controller.cancel_path()

    def cancel_movement(self) -> None:
        self.path_controller.cancel_movement()

    def abort_movement(self, preserve_position: bool = False) -> None:
        self.path_controller.abort_movement(preserve_position)

    def update(self, time_delta: float) -> None:
        """
        Handles NPC movement updates, including animations, physics, and
        navigation.

        This method updates:
        - Physics calculations for movement.
        - Animation state of the NPC.
        - Movement logic, including path progression and direct movement
            requests.

        Parameters:
            time_delta: The time elapsed since the last update
            (from clock.tick()/1000.0).
        """
        # Update sprite animations based on movement state.
        self.sprite_controller.update(time_delta)
        self.update_physics(time_delta)
        self.path_controller.update(time_delta)

    def pos_update(self) -> None:
        """WIP.  Required to be called after position changes."""
        self.tile_pos = vector2_to_tile_pos(proj(self.position))
        self.network_notify_location_change()

    def network_notify_start_moving(self, direction: Direction) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.network = self.client.network_manager
        if self.network.is_connected():
            assert self.network.client
            self.network.client.update_player(
                direction, event_type="CLIENT_MOVE_START"
            )

    def network_notify_stop_moving(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.network = self.client.network_manager
        if self.network.is_connected():
            assert self.network.client
            self.network.client.update_player(
                self.facing, event_type="CLIENT_MOVE_COMPLETE"
            )

    def network_notify_location_change(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.update_location = True
