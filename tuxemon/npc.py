# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Mapping, Sequence
from math import hypot
from typing import TYPE_CHECKING, Any, Optional, TypedDict

from tuxemon import prepare
from tuxemon.battle import Battle, decode_battle, encode_battle
from tuxemon.boxes import ItemBoxes, MonsterBoxes
from tuxemon.db import Direction, db
from tuxemon.entity import Entity
from tuxemon.item.item import Item, decode_items, encode_items
from tuxemon.locale import T
from tuxemon.map import dirs2, get_direction, proj
from tuxemon.map_view import SpriteController
from tuxemon.math import Vector2
from tuxemon.mission import MissionController
from tuxemon.money import MoneyController
from tuxemon.monster import Monster, decode_monsters, encode_monsters
from tuxemon.movement import get_tile_moverate
from tuxemon.relationship import (
    Relationships,
    decode_relationships,
    encode_relationships,
)
from tuxemon.session import Session
from tuxemon.step_tracker import StepTrackerManager, decode_steps, encode_steps
from tuxemon.technique.technique import Technique
from tuxemon.teleporter import TeleportFaint
from tuxemon.tools import vector2_to_tile_pos
from tuxemon.tracker import TrackingData, decode_tracking, encode_tracking
from tuxemon.tuxepedia import Tuxepedia, decode_tuxepedia, encode_tuxepedia

if TYPE_CHECKING:
    from tuxemon.economy import Economy
    from tuxemon.states.world.worldstate import WorldState


logger = logging.getLogger(__name__)


class NPCState(TypedDict, total=False):
    current_map: str
    facing: Direction
    game_variables: dict[str, Any]
    battles: Sequence[Mapping[str, Any]]
    tuxepedia: Mapping[str, Any]
    relationships: Mapping[str, Any]
    money: Mapping[str, Any]
    template: dict[str, Any]
    missions: Sequence[Mapping[str, Any]]
    items: Sequence[Mapping[str, Any]]
    monsters: Sequence[Mapping[str, Any]]
    player_name: str
    player_steps: float
    monster_boxes: dict[str, Sequence[Mapping[str, Any]]]
    item_boxes: dict[str, Sequence[Mapping[str, Any]]]
    tile_pos: tuple[int, int]
    teleport_faint: tuple[str, int, int]
    tracker: Mapping[str, Any]
    step_tracker: Mapping[str, Any]


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

    party_limit = prepare.PARTY_LIMIT

    def __init__(
        self,
        npc_slug: str,
        *,
        world: WorldState,
    ) -> None:
        super().__init__(slug=npc_slug, world=world)

        # load initial data from the npc database
        npc_data = db.lookup(npc_slug, table="npc")
        self.template = npc_data.template

        # This is the NPC's name to be used in dialog
        self.name = T.translate(self.slug)

        # general
        self.behavior: Optional[str] = "wander"  # not used for now
        self.game_variables: dict[str, Any] = {}  # Tracks the game state
        self.battles: list[Battle] = []  # Tracks the battles
        self.forfeit: bool = False
        # Tracks Tuxepedia (monster seen or caught)
        self.tuxepedia = Tuxepedia()
        self.relationships = Relationships()
        self.money_controller = MoneyController(self)
        # list of ways player can interact with the Npc
        self.interactions: Sequence[str] = []
        # menu labels (world menu)
        self.menu_save: bool = True
        self.menu_load: bool = True
        self.menu_player: bool = True
        self.menu_monsters: bool = True
        self.menu_bag: bool = True
        self.menu_missions: bool = True
        # This is a list of tuxemon the npc has. Do not modify directly
        self.monsters: list[Monster] = []
        # The player's items.
        self.items: list[Item] = []
        self.mission_controller = MissionController(self)
        self.economy: Optional[Economy] = None
        self.teleport_faint = TeleportFaint()
        self.tracker = TrackingData()
        self.step_tracker = StepTrackerManager()
        # Variables for long-term item and monster storage
        # Keeping these separate so other code can safely
        # assume that all values are lists
        self.monster_boxes = MonsterBoxes()
        self.item_boxes = ItemBoxes()
        self.pending_evolutions: list[tuple[Monster, Monster]] = []
        self.moves: Sequence[Technique] = []  # list of techniques
        self.steps: float = 0.0

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

        # movement related
        # Set this value to move the npc (see below)
        self.move_direction: Optional[Direction] = None
        # Set this value to change the facing direction
        self.ignore_collisions = False

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction until it is set to None.
        self.sprite_controller = SpriteController(self)

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
            "facing": self.facing,
            "game_variables": self.game_variables,
            "battles": encode_battle(self.battles),
            "tuxepedia": encode_tuxepedia(self.tuxepedia),
            "relationships": encode_relationships(self.relationships),
            "money": dict(),
            "items": encode_items(self.items),
            "template": self.template.model_dump(),
            "missions": self.mission_controller.encode_missions(),
            "monsters": encode_monsters(self.monsters),
            "player_name": self.name,
            "player_steps": self.steps,
            "monster_boxes": dict(),
            "item_boxes": dict(),
            "tile_pos": self.tile_pos,
            "teleport_faint": self.teleport_faint.to_tuple(),
            "tracker": encode_tracking(self.tracker),
            "step_tracker": encode_steps(self.step_tracker),
        }

        self.monster_boxes.save(state)
        self.item_boxes.save(state)
        state["money"] = self.money_controller.save()

        return state

    def set_state(self, session: Session, save_data: NPCState) -> None:
        """
        Recreates npc from saved data.

        Parameters:
            session: Game session.
            save_data: Data used to recreate the NPC.
        """
        self.set_facing(Direction(save_data.get("facing", "down")))
        self.game_variables = save_data["game_variables"]
        self.tuxepedia = decode_tuxepedia(save_data["tuxepedia"])
        self.relationships = decode_relationships(save_data["relationships"])
        self.battles = []
        for battle in decode_battle(save_data.get("battles")):
            self.battles.append(battle)
        self.items = []
        for item in decode_items(save_data.get("items")):
            self.add_item(item)
        self.monsters = []
        for monster in decode_monsters(save_data.get("monsters")):
            self.add_monster(monster, len(self.monsters))
        self.mission_controller.decode_missions(save_data.get("missions"))
        self.name = save_data["player_name"]
        self.steps = save_data["player_steps"]
        self.money_controller.load(save_data)
        self.monster_boxes.load(save_data)
        self.item_boxes.load(save_data)

        self.teleport_faint = TeleportFaint.from_tuple(
            save_data["teleport_faint"]
        )

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
        path = self.world.pathfind(self.tile_pos, destination, self.facing)
        if path:
            self.path = list(path)
            self.next_waypoint()

    def check_continue(self) -> None:
        try:
            tile = self.world.client.map_manager.collision_map[self.tile_pos]
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
            self.move_direction = None
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
        self.move_direction = None
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
        surface_map = self.world.client.map_manager.surface_map
        direction = get_direction(proj(self.position), target)
        self.set_facing(direction)
        try:
            if self.world.pathfinder.is_tile_traversable(self, target):
                moverate = get_tile_moverate(surface_map, self, target)
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
                self.mover.move(self.mover.current_direction, moverate)
                self.remove_collision()
            else:
                self.stop_moving()
                self.handle_obstruction(target)
        except Exception as e:
            logger.error(f"Error in next_waypoint for {self.slug}: {e}")
            self.cancel_path()

    def handle_obstruction(self, target: tuple[int, int]) -> None:
        if self.pathfinding:
            npc = self.world.get_entity_pos(self.pathfinding)
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
            self.check_continue()
            if self.path:
                self.next_waypoint()

    def pos_update(self) -> None:
        """WIP.  Required to be called after position changes."""
        self.tile_pos = vector2_to_tile_pos(proj(self.position))
        self.network_notify_location_change()

    def network_notify_start_moving(self, direction: Direction) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.network = self.world.client.network_manager
        if self.network.is_connected():
            assert self.network.client
            self.network.client.update_player(
                direction, event_type="CLIENT_MOVE_START"
            )

    def network_notify_stop_moving(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.network = self.world.client.network_manager
        if self.network.is_connected():
            assert self.network.client
            self.network.client.update_player(
                self.facing, event_type="CLIENT_MOVE_COMPLETE"
            )

    def network_notify_location_change(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.update_location = True

    ####################################################
    #                   Monsters                       #
    ####################################################
    def add_monster(self, monster: Monster, slot: int) -> None:
        """
        Adds a monster to the npc's list of monsters.

        If the player's party is full, it will send the monster to
        PCState archive.

        Parameters:
            monster: The monster to add to the npc's party.
        """
        kennel = prepare.KENNEL

        monster.owner = self
        if len(self.monsters) >= self.party_limit:
            self.monster_boxes.add_monster(kennel, monster)
            if self.monster_boxes.is_box_full(kennel):
                self.monster_boxes.create_and_merge_box(kennel)
        else:
            self.monsters.insert(slot, monster)

    def find_monster(self, monster_slug: str) -> Optional[Monster]:
        """
        Finds a monster in the npc's list of monsters.

        Parameters:
            monster_slug: The slug name of the monster.

        Returns:
            Monster found.
        """
        for monster in self.monsters:
            if monster.slug == monster_slug:
                return monster

        return None

    def find_monster_by_id(self, instance_id: uuid.UUID) -> Optional[Monster]:
        """
        Finds a monster in the npc's list which has the given id.

        Parameters:
            instance_id: The instance_id of the monster.

        Returns:
            Monster found, or None.
        """
        return next(
            (m for m in self.monsters if m.instance_id == instance_id), None
        )

    def release_monster(self, monster: Monster) -> bool:
        """
        Releases a monster from this npc's party. Used to release into wild.

        Parameters:
            monster: Monster to release into the wild.
        """
        if len(self.monsters) == 1:
            return False

        if monster in self.monsters:
            self.monsters.remove(monster)
            return True
        else:
            return False

    def remove_monster(self, monster: Monster) -> None:
        """
        Removes a monster from this npc's party.

        Parameters:
            monster: Monster to remove from the npc's party.
        """
        if monster in self.monsters:
            self.monsters.remove(monster)

    def switch_monsters(self, index_1: int, index_2: int) -> None:
        """
        Swap two monsters in this npc's party.

        Parameters:
            index_1: The indexes of the monsters to switch in the npc's party.
            index_2: The indexes of the monsters to switch in the npc's party.
        """
        self.monsters[index_1], self.monsters[index_2] = (
            self.monsters[index_2],
            self.monsters[index_1],
        )

    def has_tech(self, tech: str) -> bool:
        """
        Returns TRUE if there is the technique in the party.

        Parameters:
            tech: The slug name of the technique.
        """
        for technique in self.monsters:
            for move in technique.moves:
                if move.slug == tech:
                    return True
        return False

    def has_type(self, element: str) -> bool:
        """
        Returns TRUE if there is the type in the party.
        """
        return any(mon.has_type(element) for mon in self.monsters)

    ####################################################
    #                      Items                       #
    ####################################################
    def add_item(self, item: Item) -> None:
        """
        Adds an item to the npc's bag.

        If the player's bag is full, it will send the item to
        PCState archive.
        """
        locker = prepare.LOCKER
        # it creates the locker
        if not self.item_boxes.has_box(locker, "item"):
            self.item_boxes.create_box(locker, "item")

        if len(self.items) >= prepare.MAX_TYPES_BAG:
            self.item_boxes.add_item(locker, item)
        else:
            self.items.append(item)

    def remove_item(self, item: Item) -> None:
        """
        Removes an item from this npc's bag.
        """
        if item in self.items:
            self.items.remove(item)

    def find_item(self, item_slug: str) -> Optional[Item]:
        """
        Finds an item in the npc's bag.
        """
        for itm in self.items:
            if itm.slug == item_slug:
                return itm

        return None

    def find_item_by_id(self, instance_id: uuid.UUID) -> Optional[Item]:
        """
        Finds an item in the npc's bag which has the given id.
        """
        return next(
            (m for m in self.items if m.instance_id == instance_id), None
        )
