# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from math import hypot
from typing import TYPE_CHECKING, Any, Optional, TypedDict

from tuxemon import prepare
from tuxemon.battle import BattlesHandler
from tuxemon.boxes import ItemBoxes, MonsterBoxes
from tuxemon.db import DialogueProfile, Direction, NpcModel, db
from tuxemon.entity import Entity
from tuxemon.item.item import Item, decode_items, encode_items
from tuxemon.locale import T
from tuxemon.map import dirs2, get_direction, proj
from tuxemon.map_view import SpriteController
from tuxemon.math import Vector2
from tuxemon.mission.controller import MissionController
from tuxemon.mission.manager import MissionManager
from tuxemon.money import MoneyController
from tuxemon.monster import Monster, decode_monsters, encode_monsters
from tuxemon.monster_dir.evolution_registry import EvolutionRegistry
from tuxemon.movement import get_tile_moverate
from tuxemon.relationship import (
    Relationships,
    decode_relationships,
    encode_relationships,
)
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
    unlocked_letters: Mapping[str, Any]
    evolution_registry: Mapping[str, Any]


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
        self.game_variables: dict[str, Any] = {}  # Tracks the game state
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
        self.items = NPCBagHandler(item_boxes=self.item_boxes)
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
            "facing": self.facing,
            "game_variables": self.game_variables,
            "battles": self.battle_handler.encode_battle(),
            "tuxepedia": encode_tuxepedia(self.tuxepedia),
            "relationships": encode_relationships(self.relationships),
            "money": self.money_controller.save(),
            "items": self.items.encode_items(),
            "template": self.template.model_dump(),
            "missions": self.mission_controller.encode_missions(),
            "monsters": self.party.encode_party(),
            "player_name": self.name,
            "player_steps": self.steps,
            "monster_boxes": self.monster_boxes.get_state(),
            "item_boxes": self.item_boxes.get_state(),
            "tile_pos": self.tile_pos,
            "teleport_faint": self.teleport_faint.to_tuple(),
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
        self.game_variables = save_data["game_variables"]
        self.tuxepedia = decode_tuxepedia(save_data["tuxepedia"])
        self.relationships = decode_relationships(save_data["relationships"])
        self.battle_handler.decode_battle(save_data)
        self.items.decode_items(save_data)
        self.party.decode_party(save_data)
        self.mission_controller.decode_missions(save_data.get("missions"))
        self.name = save_data["player_name"]
        self.steps = save_data["player_steps"]
        self.money_controller.load(save_data)
        self.unlocked_letters = decode_cipher(save_data)
        self.evolution_registry.decode_registry(
            save_data.get("evolution_registry", {})
        )
        self.monster_boxes.load(self, save_data)
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
        surface_map = self.client.map_manager.surface_map
        direction = get_direction(proj(self.position), target)
        self.set_facing(direction)
        try:
            if self.client.pathfinder.is_tile_traversable(self, target):
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
            self.check_continue()
            if self.path:
                self.next_waypoint()

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


class NPCBagHandler:

    def __init__(
        self,
        item_boxes: ItemBoxes,
        items: Optional[list[Item]] = None,
        bag_limit: int = prepare.MAX_TYPES_BAG,
    ) -> None:
        self._items = items if items is not None else []
        self._bag_limit = bag_limit
        self._item_boxes = item_boxes

    def add_item(
        self, item: Item, quantity: int = 1, locker: str = prepare.LOCKER
    ) -> None:
        """
        Adds an item to the NPC's bag.

        If the bag is full (based on MAX_TYPES_BAG), it will send the item to
        the PCState archive (item boxes).
        """
        logger.debug(
            f"Adding item '{item.slug}' (quantity: {quantity}) to NPC's inventory."
        )

        if not self._item_boxes.has_box(locker, "item"):
            logger.debug(
                f"Item box '{locker}' does not exist. Creating new item box."
            )
            self._item_boxes.create_box(locker, "item")

        existing = self.find_item(item.slug)
        if existing:
            new_qty = existing.quantity + quantity
            logger.debug(
                f"Item '{item.slug}' exists in inventory. Increasing quantity from {existing.quantity} to {new_qty}."
            )
            existing.set_quantity(new_qty)
        elif len(self._items) >= self._bag_limit:
            logger.debug(
                f"Bag is full. Sending item '{item.slug}' to item box '{locker}'."
            )
            item.set_quantity(quantity)
            self._item_boxes.add_item(locker, item)
        else:
            logger.debug(
                f"Item '{item.slug}' added to bag. Current total items: {len(self._items) + 1}."
            )
            item.set_quantity(quantity)
            self._items.append(item)

    def remove_item(self, item: Item, quantity: int = 1) -> bool:
        """
        Removes a quantity of an item from the NPC's bag.

        If quantity reaches zero or below, the item is fully removed.
        """
        logger.debug(
            f"Attempting to remove {quantity} of '{item.slug}' from inventory."
        )

        if quantity < 0:
            logger.warning(
                f"Tried to remove negative quantity: {quantity} for item '{item.slug}'"
            )
            return False

        if item in self._items:
            if item.quantity <= quantity:
                logger.debug(
                    f"Removing item '{item.slug}' completely (quantity: {item.quantity})."
                )
                self._items.remove(item)
            else:
                new_qty = item.quantity - quantity
                logger.debug(
                    f"Reducing quantity of '{item.slug}' from {item.quantity} to {new_qty}."
                )
                item.set_quantity(new_qty)
            return True
        logger.debug(f"Item '{item.slug}' not found in inventory.")
        return False

    def find_item(self, item_slug: str) -> Optional[Item]:
        """
        Finds the first item in the NPC's bag with the given slug.
        """
        for itm in self._items:
            if itm.slug == item_slug:
                return itm
        return None

    def get_items(self) -> list[Item]:
        return self._items

    def has_item(self, item_slug: str) -> bool:
        """
        Checks if the NPC's bag contains an item with the given slug.
        """
        return any(itm.slug == item_slug for itm in self._items)

    def find_item_by_id(self, instance_id: uuid.UUID) -> Optional[Item]:
        """
        Finds an item in the NPC's bag which has the given instance ID.
        """
        return next(
            (itm for itm in self._items if itm.instance_id == instance_id),
            None,
        )

    def clear_items(self) -> None:
        """Removes all items from the NPC's bag."""
        self._items.clear()

    def get_all_item_quantities(self) -> dict[str, int]:
        """
        Returns a dictionary mapping item slugs to their total quantities
        in the NPC's bag. This provides a 'count-based view' of the bag.
        """
        quantities: dict[str, int] = {}
        for item in self._items:
            quantities[item.slug] = item.quantity
        return quantities

    def encode_items(self) -> Sequence[Mapping[str, Any]]:
        return encode_items(self._items)

    def decode_items(self, json_data: Optional[Mapping[str, Any]]) -> None:
        if json_data and "items" in json_data:
            self._items = [itm for itm in decode_items(json_data["items"])]


class PartyHandler:
    """
    Manages a NPC's party, including adding, removing, finding,
    and switching monsters.
    """

    def __init__(
        self,
        monster_boxes: MonsterBoxes,
        owner: NPC,
        monsters: Optional[list[Monster]] = None,
        party_limit: int = prepare.PARTY_LIMIT,
    ) -> None:
        self._monsters = monsters if monsters is not None else []
        self._party_limit = party_limit
        self._monster_boxes = monster_boxes
        self._owner = owner

    @property
    def monsters(self) -> list[Monster]:
        """Returns the list of monsters in the party."""
        return self._monsters

    @property
    def party_size(self) -> int:
        """Returns the current number of monsters in the party."""
        return len(self._monsters)

    @property
    def party_limit(self) -> int:
        """Returns the maximum number of monsters allowed in the party."""
        return self._party_limit

    @property
    def level_lowest(self) -> Optional[int]:
        """Returns the lowest level among monsters in the party, or None if empty."""
        if not self._monsters:
            return None
        return min(mon.level for mon in self._monsters)

    @property
    def level_highest(self) -> Optional[int]:
        """Returns the highest level among monsters in the party, or None if empty."""
        if not self._monsters:
            return None
        return max(mon.level for mon in self._monsters)

    @property
    def level_average(self) -> Optional[int]:
        """Returns the average level of monsters in the party, or None if empty."""
        if not self._monsters:
            return None
        total = sum(mon.level for mon in self._monsters)
        return round(total / len(self._monsters))

    def add_monster(
        self,
        monster: Monster,
        slot: Optional[int] = None,
        kennel: str = prepare.KENNEL,
    ) -> None:
        """
        Adds a monster to the party. If the party is full, it sends the monster
        to the monster boxes (PCState archive).

        Parameters:
            monster: The monster to add.
            slot: Optional. The index to insert the monster at. If None or
                  party is full, it's added to the end or sent to boxes.
        """
        monster.set_owner(self._owner)

        if self.party_size >= self._party_limit:
            self._monster_boxes.add_monster(kennel, monster)
            if self._monster_boxes.is_box_full(kennel):
                self._monster_boxes.create_and_merge_box(kennel)
        else:
            if slot is not None and 0 <= slot <= self.party_size:
                self._monsters.insert(slot, monster)
            else:
                self._monsters.append(monster)

    def find_monster(self, monster_slug: str) -> Optional[Monster]:
        """
        Finds a monster in the party by its slug.

        Parameters:
            monster_slug: The slug name of the monster.

        Returns:
            Monster found, or None.
        """
        for monster in self._monsters:
            if monster.slug == monster_slug:
                return monster
        return None

    def find_monster_by_id(self, instance_id: uuid.UUID) -> Optional[Monster]:
        """
        Finds a monster in the party by its instance ID.

        Parameters:
            instance_id: The instance_id of the monster.

        Returns:
            Monster found, or None.
        """
        return next(
            (m for m in self._monsters if m.instance_id == instance_id), None
        )

    def release_monster(self, monster: Monster) -> bool:
        """
        Releases a monster from this party. Used to release into the wild.
        Prevents releasing the last monster if the party is not empty.

        Parameters:
            monster: Monster to release into the wild.

        Returns:
            True if the monster was successfully released, False otherwise.
        """
        if self.party_size <= 1:
            return False

        if monster in self._monsters:
            self.remove_monster(monster)
            monster.owner = None
            return True
        else:
            return False

    def remove_monster(self, monster: Monster) -> None:
        """
        Removes a monster from this party.

        Parameters:
            monster: Monster to remove from the party.
        """
        if monster in self._monsters:
            self._monsters.remove(monster)

    def switch_monsters(self, index_1: int, index_2: int) -> None:
        """
        Swaps two monsters in this party by their indices.

        Parameters:
            index_1: The index of the first monster.
            index_2: The index of the second monster.
        """
        if not (
            0 <= index_1 < self.party_size and 0 <= index_2 < self.party_size
        ):
            raise IndexError("Indices out of bounds for party size.")

        self._monsters[index_1], self._monsters[index_2] = (
            self._monsters[index_2],
            self._monsters[index_1],
        )

    def has_monster(self, monster: Monster) -> bool:
        """
        Checks if a given monster is in the party.

        Parameters:
            monster: The monster to check.

        Returns:
            True if the monster is in the party, False otherwise.
        """
        return monster in self._monsters

    def has_tech(self, tech_slug: str) -> bool:
        """
        Returns True if any monster in the party has the given technique.

        Parameters:
            tech_slug: The slug name of the technique.
        """
        for monster in self._monsters:
            if monster.moves.has_move(tech_slug):
                return True
        return False

    def replace_monster(
        self, old_monster: Monster, new_monster: Monster
    ) -> bool:
        """
        Replaces an existing monster in the party with a new one.

        Parameters:
            old_monster: The monster to replace.
            new_monster: The new monster.

        Returns:
            True if successful, False otherwise.
        """
        if old_monster in self._monsters:
            index = self._monsters.index(old_monster)
            self._monsters[index] = new_monster
            new_monster.owner = self._owner
            return True
        return False

    def has_type(self, element_slug: str) -> bool:
        """
        Returns True if any monster in the party has the given type.
        """
        return any(mon.has_type(element_slug) for mon in self._monsters)

    def clear_party(self) -> None:
        """
        Removes all monsters from the party and clears their ownership.
        """
        if self._monsters:
            for monster in self._monsters:
                monster.owner = None
        self._monsters.clear()

    def get_alignment(self) -> Optional[str]:
        """
        Returns the dominant elemental type in the party,
        based on the most frequently occurring type among monsters.
        If no types are found, returns None.
        """
        type_counter: Counter[str] = Counter()

        for monster in self._monsters:
            try:
                type_slugs = monster.types.get_type_slugs()
                type_counter.update(type_slugs)
            except Exception:
                continue  # Skip if the monster has no types

        if not type_counter:
            return None

        dominant_type, _ = type_counter.most_common(1)[0]
        return dominant_type

    def encode_party(self) -> Sequence[Mapping[str, Any]]:
        return encode_monsters(self._monsters)

    def decode_party(self, json_data: Optional[Mapping[str, Any]]) -> None:
        self.clear_party()
        if json_data and "monsters" in json_data:
            for mon in decode_monsters(json_data["monsters"]):
                self.add_monster(mon, self.party_size)
