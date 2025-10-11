# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from math import hypot
from typing import TYPE_CHECKING, Optional

from tuxemon.boxes import ItemBoxes, MonsterBoxes
from tuxemon.db import DialogueProfile, Direction, NpcModel, db
from tuxemon.entity import Entity
from tuxemon.entity_dir.bag import BagHandler
from tuxemon.entity_dir.battle import BattlesHandler
from tuxemon.entity_dir.party import PartyHandler
from tuxemon.game_variables import GameVariablesManager, PlayerVariablesManager
from tuxemon.locale import T
from tuxemon.map.map import dirs2, get_direction, proj
from tuxemon.map.map_view import SpriteController
from tuxemon.math import Vector2
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


def tile_distance(tile0: Iterable[float], tile1: Iterable[float]) -> float:
    x0, y0 = tile0
    x1, y1 = tile1
    return hypot(x1 - x0, y1 - y0)


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

        # pathfinding and waypoint related
        self.pathfinding: Optional[tuple[int, int]] = None
        self.path: list[tuple[int, int]] = []
        # Stores the final destination sent from a client
        self.final_move_dest = [0, 0]

        # This is used to 'set back' when lost, and make movement robust.
        # If entity falls off of map due to a bug, it can be returned to this value.
        # When moving to a waypoint, this is used to detect if movement has overshot
        # the destination due to speed issues or framerate jitters.
        self.path_origin: Optional[tuple[int, int]] = None

        self.sprite_controller = SpriteController(self)

    @property
    def game_variables(self) -> PlayerVariablesManager:
        return self._variables.player

    @property
    def monsters(self) -> list[Monster]:
        """Returns the list of monsters in the party."""
        return self.party.monsters

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

        _template = save_data["template"]
        self.template.slug = _template["slug"]
        self.template.sprite_name = _template["sprite_name"]
        self.template.combat_front = _template["combat_front"]
        self.sprite_controller.load_sprites(self.template)

    def pathfind(self, destination: tuple[int, int]) -> None:
        """
        Find a path and also start it.

        If asked to pathfind, an NPC will pathfind until it:
        * reaches the destination
        * NPC.cancel_movement() is called

        If blocked, the NPC will wait until it is able to move.

        Queries the world for a valid path.

        Parameters:
            destination: Desired final position.
        """
        self.pathfinding = destination
        path = self.client.pathfinder.pathfind(
            self.tile_pos, destination, self.facing
        )
        if path:
            self.path = list(path)
            self.next_waypoint()

    def check_continue(self) -> None:
        try:
            tile = self.client.map_manager.collision_map[self.tile_pos]
            if tile and tile.endure:
                _direction = (
                    self.facing if len(tile.endure) > 1 else tile.endure[0]
                )
                self.move_one_tile(_direction)
            else:
                pass
        except (KeyError, TypeError):
            pass

    def cancel_path(self) -> None:
        """
        Clears all active pathfinding data and stops the NPC's movement.

        This method removes the NPC's current path and resets pathfinding
        related attributes, ensuring no further automatic movement occurs.
        """
        self.path = []
        self.pathfinding = None
        self.path_origin = None

    def cancel_movement(self) -> None:
        """
        Stops the NPC's movement and adjusts pathfinding logic if necessary.

        If the NPC is currently following a path but hasn't reached the
        destination, it retains the last waypoint to avoid abrupt stopping.
        Otherwise, all movement is halted and pathfinding is cleared.
        """
        if proj(self.position) == self.path_origin:
            # we *just* started a new path; discard it and stop
            self.abort_movement(preserve_position=True)
        elif self.path and self.moving:
            # we are in the middle of moving between tiles
            self.path = [self.path[-1]]
            self.pathfinding = None
            self.set_move_direction()
        else:
            self.abort_movement()

    def abort_movement(self, preserve_position: bool = False) -> None:
        """
        Safely halts all movement-related actions for the NPC.

        This method ensures that the NPC stops moving, cancels any
        active pathfinding, and resets its movement direction. If
        `preserve_position` is True, the NPC's current tile position
        is retained; otherwise, it reverts to its last recorded origin.
        """
        if not preserve_position and self.path_origin is not None:
            self.tile_pos = self.path_origin
        self.set_move_direction()
        self.stop_moving()
        self.cancel_path()

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
        if self.path or self.move_direction:
            self.process_movement()

    def process_movement(self) -> None:
        """
        Manages NPC movement logic, handling pathfinding, waypoint progression,
        and obstructions.

        This method ensures smooth movement by:
        - Initiating pathfinding if needed.
        - Progressing through waypoints.
        - Responding to blocked paths or missing destinations.
        - Handling direct movement requests when no path exists.

        If movement is blocked or invalid, appropriate cancellation routines
        are triggered.
        """
        # Start pathfinding if NPC is assigned a destination but no path
        # is found yet.
        if self.pathfinding and not self.path:
            self.pathfind(self.pathfinding)
            return

        # If NPC has a valid path, proceed with movement.
        if self.path:
            if self.path_origin:
                # If path origin is set, NPC has started moving from one
                # tile to another.
                self.check_waypoint()
            else:
                # If path origin isn't set, previous waypoint change failed
                # try again.
                self.next_waypoint()

        # Direct movement request handling—NPC moves manually if pathfinding
        # isn't involved.
        if self.move_direction:
            if self.path and not self.moving:
                # NPC wants to move but is blocked—cancel movement path.
                self.cancel_path()

            if not self.path:
                # No path available—initiate direct movement.
                self.move_one_tile(self.move_direction)
                self.next_waypoint()

        # TODO: Implement logic for external forces affecting movement.
        # TODO: Currently, this method only accounts for explicitly
        # controlled movement.
        # TODO: Physics-based movement is not possible since this halts
        # that action.

        # If NPC has no remaining path, stop movement and animation.
        if not self.path:
            self.cancel_movement()
            self.sprite_controller.stop_animation()

    def move_one_tile(self, direction: Direction) -> None:
        """
        Ask entity to move one tile.

        Parameters:
            direction: Direction where to move.
        """
        target = Vector2(self.tile_pos) + dirs2[direction]
        self.path.append(vector2_to_tile_pos(target))

    def move_multiple_tiles(self, direction: Direction, strength: int) -> None:
        """
        Attempts to move the entity multiple tiles in the specified direction,
        up to the given strength.

        This method checks tile-by-tile whether movement is allowed using the
        pathfinder's exit logic.
        If a tile is blocked, movement stops at the last valid position. The
        resulting path is reversed before being appended to ensure that the
        next waypoint is always the immediate neighbor, since movement logic
        expects self.path[-1] to be adjacent to the current position.

        Parameters:
            direction: The direction in which to move.
            strength: The maximum number of tiles to attempt moving through.
        """
        self.set_facing(direction)

        origin = self.path[-1] if self.path else self.tile_pos
        steps: list[tuple[int, int]] = []

        for _ in range(strength):
            candidate = vector2_to_tile_pos(Vector2(origin) + dirs2[direction])

            if candidate == origin:
                continue

            exits = self.client.pathfinder.get_exits(origin, direction)
            logger.debug(
                f"Valid exits from {origin} facing {direction}: {exits}"
            )
            if candidate not in exits:
                logger.debug(
                    f"Tile blocked: {candidate} from {origin} facing {direction}"
                )
                break

            steps.append(candidate)
            origin = candidate

        if steps:
            self.path.extend(reversed(steps))
            self.path_origin = self.tile_pos
            logger.debug(
                f"Final path (last is next): {self.path} | path_origin={self.path_origin}"
            )
            self.next_waypoint()

    @property
    def move_destination(self) -> Optional[tuple[int, int]]:
        """Only used for the char_moved condition."""
        if self.path:
            return self.path[-1]
        else:
            return None

    def next_waypoint(self) -> None:
        """
        Take the next step of the path, stop if way is blocked.

        * This must be called after a path is set
        * Not needed to be called if existing path is modified
        * If the next waypoint is blocked, the waypoint will be removed
        """
        target = self.path[-1]
        direction = get_direction(proj(self.position), target)
        self.set_facing(direction)
        try:
            if self.client.pathfinder.is_tile_traversable(
                self.tile_pos, self.facing, target, self.ignore_collisions
            ):
                # Surfanim suffers from significant clock drift, causing
                # timing inconsistencies. Even after completing one animation
                # cycle, the timing can become inaccurate. This drift results
                # in walking steps misaligning with tile positions, with
                # certain frames lasting only a single game frame.
                # Using `play` to initiate each tile transition helps reset
                # the surfanim timer, keeping walking animation frames in sync.
                # However, occasional desynchronization still occurs.
                # To fully resolve this issue, the game will eventually need
                # a dedicated global clock—not reliant on wall time—to eliminate
                # visual glitches and ensure frame accuracy.
                self.sprite_controller.play_animation()
                self.path_origin = self.tile_pos
                self.mover.move(self.mover.current_direction)
                self.remove_collision()
            else:
                self.stop_moving()
                self.handle_obstruction(target)
        except Exception as e:
            logger.error(f"Error in next_waypoint for {self.slug}: {e}")
            self.cancel_path()

    def handle_obstruction(self, target: tuple[int, int]) -> None:
        if self.pathfinding:
            npc = self.client.npc_manager.get_entity_pos(self.pathfinding)
            if npc:
                logger.info(
                    f"{npc.slug} obstructing {self.slug}, recalculating path."
                )
                self.pathfind(self.pathfinding)
            else:
                logger.warning(
                    f"{self.slug} could not proceed to {self.pathfinding} due to obstruction. "
                    "Consider splitting pathfinding or postponing movement."
                )
        else:
            logger.debug(
                f"{self.slug} faced obstruction at {target}. Movement stopped."
            )

    def check_waypoint(self) -> None:
        """
        Check if the waypoint is reached and sets new waypoint if so.

        * For most accurate speed, tests distance traveled.
        * Doesn't verify the target position, just distance
        * Assumes once waypoint is set, direction doesn't change
        * Honors continue tiles
        """
        target = self.path[-1]
        assert self.path_origin
        expected = tile_distance(self.path_origin, target)
        traveled = tile_distance(proj(self.position), self.path_origin)
        if traveled >= expected:
            self.set_position(target)
            self.path.pop()
            self.path_origin = None

            self.check_tile_properties()

            self.check_continue()
            if self.path:
                self.next_waypoint()

    def check_tile_properties(self) -> None:
        """
        Checks the current tile properties and applies them if found.
        """
        try:
            tile = self.client.map_manager.collision_map.get(self.tile_pos)
            if tile is None:
                return  # No tile found, nothing to apply

            if tile.push_effect:
                self.move_multiple_tiles(
                    direction=tile.push_effect.direction,
                    strength=tile.push_effect.strength,
                )

            if tile.speed_modifier:
                self.set_moverate_modifier(tile.speed_modifier)

        except (KeyError, TypeError):
            pass

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
