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
from tuxemon.map import dirs2, dirs3, get_direction, proj
from tuxemon.map_view import SpriteRenderer
from tuxemon.math import Vector2
from tuxemon.mission import MissionManager
from tuxemon.money import MoneyController
from tuxemon.monster import Monster, decode_monsters, encode_monsters
from tuxemon.prepare import CONFIG
from tuxemon.session import Session
from tuxemon.technique.technique import Technique
from tuxemon.tools import vector2_to_tile_pos
from tuxemon.tuxepedia import Tuxepedia, decode_tuxepedia, encode_tuxepedia

if TYPE_CHECKING:
    from tuxemon.economy import Economy
    from tuxemon.states.world.worldstate import WorldState


logger = logging.getLogger(__name__)


class NPCState(TypedDict):
    current_map: str
    facing: Direction
    game_variables: dict[str, Any]
    battles: Sequence[Mapping[str, Any]]
    tuxepedia: Mapping[str, Any]
    contacts: dict[str, str]
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
        self.contacts: dict[str, str] = {}
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
        self.mission_manager = MissionManager(self)
        self.economy: Optional[Economy] = None
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
        self.facing = Direction.down
        self.moverate = CONFIG.player_walkrate  # walk by default
        self.ignore_collisions = False

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction until it is set to None.
        self.sprite_renderer = SpriteRenderer(self)

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
            "contacts": self.contacts,
            "money": dict(),
            "items": encode_items(self.items),
            "template": self.template.model_dump(),
            "missions": self.mission_manager.encode_missions(),
            "monsters": encode_monsters(self.monsters),
            "player_name": self.name,
            "player_steps": self.steps,
            "monster_boxes": dict(),
            "item_boxes": dict(),
            "tile_pos": self.tile_pos,
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
        self.facing = Direction(save_data.get("facing", "down"))
        self.game_variables = save_data["game_variables"]
        self.tuxepedia = decode_tuxepedia(save_data["tuxepedia"])
        self.contacts = save_data["contacts"]
        self.battles = []
        for battle in decode_battle(save_data.get("battles")):
            self.battles.append(battle)
        self.items = []
        for item in decode_items(save_data.get("items")):
            self.add_item(item)
        self.monsters = []
        for monster in decode_monsters(save_data.get("monsters")):
            self.add_monster(monster, len(self.monsters))
        self.mission_manager.load_missions(save_data.get("missions"))
        self.name = save_data["player_name"]
        self.steps = save_data["player_steps"]
        self.money_controller.load(save_data)
        self.monster_boxes.load(save_data)
        self.item_boxes.load(save_data)

        _template = save_data["template"]
        self.template.slug = _template["slug"]
        self.template.sprite_name = _template["sprite_name"]
        self.template.combat_front = _template["combat_front"]
        self.sprite_renderer._load_sprites()

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
        path = self.world.pathfind(self.tile_pos, destination)
        if path:
            self.path = list(path)
            self.next_waypoint()

    def check_continue(self) -> None:
        try:
            tile = self.world.collision_map[self.tile_pos]
            if tile and tile.endure:
                _direction = (
                    self.facing if len(tile.endure) > 1 else tile.endure[0]
                )
                self.move_one_tile(_direction)
            else:
                pass
        except (KeyError, TypeError):
            pass

    def stop_moving(self) -> None:
        """
        Completely stop all movement.

        Be careful, if stopped while in the path, it might not be tile-aligned.

        May continue if move_direction is set.

        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def cancel_path(self) -> None:
        """
        Stop following a path.

        NPC may still continue to move if move_direction has been set.

        """
        self.path = []
        self.pathfinding = None
        self.path_origin = None

    def cancel_movement(self) -> None:
        """
        Gracefully stop moving.  If in a path, then will finish tile movement.

        Generally, use this if you want to stop.  Will stop at a tile coord.

        """
        self.move_direction = None
        if proj(self.position3) == self.path_origin:
            # we *just* started a new path; discard it and stop
            self.abort_movement()
        elif self.path and self.moving:
            # we are in the middle of moving between tiles
            self.path = [self.path[-1]]
            self.pathfinding = None
        else:
            # probably already stopped, just clear the path
            self.stop_moving()
            self.cancel_path()

    def abort_movement(self) -> None:
        """
        Stop moving, cancel paths, and reset tile position to center.

        The tile position will be truncated, so even if there is another
        closer tile, it will always return the tile where movement
        started.

        This is a useful method if you want to abort a path movement
        and also don't want to advance to another tile.

        """
        if self.path_origin is not None:
            self.tile_pos = self.path_origin
        self.move_direction = None
        self.stop_moving()
        self.cancel_path()

    def update(self, time_delta: float) -> None:
        """
        Update the entity movement around the game world.

        * check if the move_direction variable is set
        * set the movement speed
        * follow waypoints
        * control walking animations
        * send network updates

        Parameters:
            time_delta: A float of the time that has passed since the
                last frame. This is generated by clock.tick() / 1000.0.

        """
        # update physics.  eventually move to another class
        self.sprite_renderer.update(time_delta)
        self.update_physics(time_delta)

        if self.pathfinding and not self.path:
            # wants to pathfind, but there was no path last check
            self.pathfind(self.pathfinding)
            return

        if self.path:
            if self.path_origin:
                # if path origin is set, then npc has started moving
                # from one tile to another.
                self.check_waypoint()
            else:
                # if path origin is not set, then a previous attempt to change
                # waypoints failed, so try again.
                self.next_waypoint()

        # does the npc want to move?
        if self.move_direction:
            if self.path and not self.moving:
                # npc wants to move and has a path, but it is blocked
                self.cancel_path()

            if not self.path:
                # there is no path, so start a new one
                self.move_one_tile(self.move_direction)
                self.next_waypoint()

        # TODO: determine way to tell if another force is moving the entity
        # TODO: basically, this simple check will only allow explicit npc movement
        # TODO: its not possible to move the entity with physics b/c this stops that
        if not self.path:
            self.cancel_movement()
            self.sprite_renderer.surface_animations.stop()

    def move_one_tile(self, direction: Direction) -> None:
        """
        Ask entity to move one tile.

        Parameters:
            direction: Direction where to move.

        """
        self.path.append(
            vector2_to_tile_pos(Vector2(self.tile_pos) + dirs2[direction])
        )

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
        direction = get_direction(proj(self.position3), target)
        self.facing = direction
        if self.world.pathfinder.is_tile_traversable(self, target):
            moverate = self.world.pathfinder.get_tile_moverate(self, target)
            # surfanim has horrible clock drift.  even after one animation
            # cycle, the time will be off.  drift causes the walking steps to not
            # align with tiles and some frames will only last one game frame.
            # using play to start each tile will reset the surfanim timer
            # and prevent the walking animation frames from coming out of sync.
            # it still occasionally happens though!
            # eventually, there will need to be a global clock for the game,
            # not based on wall time, to prevent visual glitches.
            self.sprite_renderer.surface_animations.play()
            self.path_origin = self.tile_pos
            self.velocity3 = moverate * dirs3[direction]
            self.remove_collision()
        else:
            # the target is blocked now
            self.stop_moving()

            if self.pathfinding:
                # check tile for npc
                npc = self.world.get_entity_pos(self.pathfinding)
                if npc:
                    # since we are pathfinding, just try a new path
                    logger.error(
                        f"{npc.slug} on your way, {self.slug} finding new path!"
                    )
                    self.pathfind(self.pathfinding)
                else:
                    logger.warning(
                        f"Possible issue of {self.slug} in {self.tile_pos}"
                        f" in its way to {self.pathfinding}!"
                        " Consider to postpone it (eg. 'wait 1') or to split"
                        f" it (eg. 'pathfind {self.tile_pos}, stop then"
                        f" pathfind {self.pathfinding})"
                    )

            else:
                # give up and wait until the target is clear again
                pass

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
        traveled = tile_distance(proj(self.position3), self.path_origin)
        if traveled >= expected:
            self.set_position(target)
            self.path.pop()
            self.path_origin = None
            self.check_continue()
            if self.path:
                self.next_waypoint()

    def pos_update(self) -> None:
        """WIP.  Required to be called after position changes."""
        self.tile_pos = vector2_to_tile_pos(proj(self.position3))
        self.network_notify_location_change()

    def network_notify_start_moving(self, direction: Direction) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.network = self.world.client.network_manager
        if self.network.isclient or self.network.ishost:
            assert self.network.client
            self.network.client.update_player(
                direction, event_type="CLIENT_MOVE_START"
            )

    def network_notify_stop_moving(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.network = self.world.client.network_manager
        if self.network.isclient or self.network.ishost:
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

    def has_tech(self, tech: Optional[str]) -> bool:
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

    def has_type(self, element: Optional[str]) -> bool:
        """
        Returns TRUE if there is the type in the party.
        """
        if element:
            return any(mon.has_type(element) for mon in self.monsters)
        return False

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
