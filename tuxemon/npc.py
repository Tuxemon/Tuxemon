# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
import uuid
from math import hypot
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)

from tuxemon import surfanim
from tuxemon.ai import AI
from tuxemon.compat import Rect
from tuxemon.db import ElementType, OutputBattle, SeenStatus, db
from tuxemon.entity import Entity
from tuxemon.graphics import load_and_scale
from tuxemon.item.item import (
    InventoryItem,
    Item,
    decode_inventory,
    encode_inventory,
)
from tuxemon.locale import T
from tuxemon.map import Direction, dirs2, dirs3, facing, get_direction, proj
from tuxemon.math import Vector2
from tuxemon.monster import (
    MAX_LEVEL,
    Monster,
    decode_monsters,
    encode_monsters,
)
from tuxemon.prepare import CONFIG
from tuxemon.session import Session
from tuxemon.states.combat.combat import EnqueuedAction
from tuxemon.technique.technique import Technique
from tuxemon.tools import vector2_to_tile_pos

if TYPE_CHECKING:
    import pygame

    from tuxemon.item.economy import Economy
    from tuxemon.states.world.worldstate import WorldState

    SpriteMap = Union[
        Mapping[str, pygame.surface.Surface],
        Mapping[str, surfanim.SurfaceAnimation],
    ]

logger = logging.getLogger(__name__)


class NPCState(TypedDict):
    current_map: str
    facing: Direction
    game_variables: Dict[str, Any]
    battle_history: Dict[str, Tuple[OutputBattle, int]]
    tuxepedia: Dict[str, SeenStatus]
    money: Dict[str, int]
    inventory: Mapping[str, Optional[int]]
    monsters: Sequence[Mapping[str, Any]]
    player_name: str
    monster_boxes: Dict[str, Sequence[Mapping[str, Any]]]
    item_boxes: Dict[str, Mapping[str, Optional[int]]]
    tile_pos: Tuple[int, int]


# reference direction and movement states to animation names
# this dictionary is kinda wip, idk
animation_mapping = {
    True: {
        "up": "back_walk",
        "down": "front_walk",
        "left": "left_walk",
        "right": "right_walk",
    },
    False: {"up": "back", "down": "front", "left": "left", "right": "right"},
}


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

    party_limit = 6  # The maximum number of tuxemon this npc can hold

    def __init__(
        self,
        npc_slug: str,
        *,
        sprite_name: Optional[str] = None,
        combat_front: Optional[str] = None,
        combat_back: Optional[str] = None,
        world: WorldState,
    ) -> None:

        super().__init__(slug=npc_slug, world=world)

        # load initial data from the npc database
        npc_data = db.lookup(npc_slug, table="npc")

        # This is the NPC's name to be used in dialog
        self.name = T.translate(self.slug)

        if sprite_name is None:
            # Try to use the sprites defined in the JSON data
            sprite_name = npc_data.sprite_name
        if combat_front is None:
            combat_front = npc_data.combat_front
        if combat_back is None:
            combat_back = npc_data.combat_back

        # Hold on the the string so it can be sent over the network
        self.sprite_name = sprite_name
        self.combat_front = combat_front
        self.combat_back = combat_back

        # general
        self.behavior: Optional[str] = "wander"  # not used for now
        self.game_variables: Dict[str, Any] = {}  # Tracks the game state
        self.battle_history: Dict[
            str, Tuple[OutputBattle, int]
        ] = {}  # Tracks the battles
        # Tracks Tuxepedia (monster seen or caught)
        self.tuxepedia: Dict[str, SeenStatus] = {}
        self.money: Dict[str, int] = {}  # Tracks money
        self.interactions: Sequence[
            str
        ] = []  # List of ways player can interact with the Npc
        self.isplayer = False  # used for various tests, idk
        self.monsters: List[
            Monster
        ] = []  # This is a list of tuxemon the npc has. Do not modify directly
        self.inventory: Dict[
            str, InventoryItem
        ] = {}  # The Player's inventory.
        self.economy: Optional[Economy] = None
        # Variables for long-term item and monster storage
        # Keeping these seperate so other code can safely
        # assume that all values are lists
        self.monster_boxes: Dict[str, List[Monster]] = {
            CONFIG.default_monster_storage_box: []
        }
        self.item_boxes: Dict[str, Mapping[str, InventoryItem]] = {}

        # combat related
        self.ai: Optional[
            AI
        ] = None  # Whether or not this player has AI associated with it
        self.speed = 10  # To determine combat order (not related to movement!)
        self.moves: Sequence[Technique] = []  # list of techniques

        # pathfinding and waypoint related
        self.pathfinding: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
        self.final_move_dest = [
            0,
            0,
        ]  # Stores the final destination sent from a client

        # This is used to 'set back' when lost, and make movement robust.
        # If entity falls off of map due to a bug, it can be returned to this value.
        # When moving to a waypoint, this is used to detect if movement has overshot
        # the destination due to speed issues or framerate jitters.
        self.path_origin: Optional[Tuple[int, int]] = None

        # movement related
        self.move_direction: Optional[
            Direction
        ] = None  # Set this value to move the npc (see below)
        self.facing: Direction = (
            "down"  # Set this value to change the facing direction
        )
        self.moverate = CONFIG.player_walkrate  # walk by default
        self.ignore_collisions = False

        # What is "move_direction"?
        # Move direction allows other functions to move the npc in a controlled way.
        # To move the npc, change the value to one of four directions: left, right, up or down.
        # The npc will then move one tile in that direction until it is set to None.

        # TODO: move sprites into renderer so class can be used headless
        self.playerHeight = 0
        self.playerWidth = 0
        self.standing: Dict[
            str, pygame.surface.Surface
        ] = {}  # Standing animation frames
        self.sprite: Dict[
            str, surfanim.SurfaceAnimation
        ] = {}  # Moving animation frames
        self.surface_animations = surfanim.SurfaceAnimationCollection()
        self.load_sprites()
        self.rect = Rect(
            (
                self.tile_pos[0],
                self.tile_pos[1],
                self.playerWidth,
                self.playerHeight,
            )
        )

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
            "battle_history": self.battle_history,
            "tuxepedia": self.tuxepedia,
            "money": self.money,
            "inventory": encode_inventory(self.inventory),
            "monsters": encode_monsters(self.monsters),
            "player_name": self.name,
            "monster_boxes": dict(),
            "item_boxes": dict(),
            "tile_pos": self.tile_pos,
        }

        for monsterkey, monstervalue in self.monster_boxes.items():
            state["monster_boxes"][monsterkey] = encode_monsters(monstervalue)

        for itemkey, itemvalue in self.item_boxes.items():
            state["item_boxes"][itemkey] = encode_inventory(itemvalue)

        return state

    def set_state(self, session: Session, save_data: NPCState) -> None:
        """
        Recreates npc from saved data.

        Parameters:
            session: Game session.
            save_data: Data used to recreate the NPC.

        """
        self.facing = save_data.get("facing", "down")
        self.game_variables = save_data["game_variables"]
        self.battle_history = save_data["battle_history"]
        self.tuxepedia = save_data["tuxepedia"]
        self.money = save_data["money"]
        self.inventory = decode_inventory(
            session, self, save_data.get("inventory", {})
        )
        self.monsters = []
        for monster in decode_monsters(save_data.get("monsters")):
            self.add_monster(monster)
        self.name = save_data["player_name"]
        for monsterkey, monstervalue in save_data["monster_boxes"].items():
            self.monster_boxes[monsterkey] = decode_monsters(monstervalue)
        for itemkey, itemvalue in save_data["item_boxes"].items():
            self.item_boxes[itemkey] = decode_inventory(
                session, self, itemvalue
            )

    def load_sprites(self) -> None:
        """Load sprite graphics."""
        # TODO: refactor animations into renderer
        # Get all of the player's standing animation images.
        self.standing = {}
        for standing_type in facing:
            filename = f"{self.sprite_name}_{standing_type}.png"
            path = os.path.join("sprites", filename)
            self.standing[standing_type] = load_and_scale(path)
        # The player's sprite size in pixels
        self.playerWidth, self.playerHeight = self.standing["front"].get_size()

        # avoid cutoff frames when steps don't line up with tile movement
        n_frames = 3
        frame_duration = (1000 / CONFIG.player_walkrate) / n_frames / 1000 * 2

        # Load all of the player's sprite animations
        anim_types = ["front_walk", "back_walk", "left_walk", "right_walk"]
        for anim_type in anim_types:
            images = [
                "sprites/{}_{}.{}.png".format(
                    self.sprite_name, anim_type, str(num).rjust(3, "0")
                )
                for num in range(4)
            ]

            frames: List[Tuple[pygame.surface.Surface, float]] = []
            for image in images:
                surface = load_and_scale(image)
                frames.append((surface, frame_duration))

            self.sprite[anim_type] = surfanim.SurfaceAnimation(
                frames, loop=True
            )

        # Have the animation objects managed by a SurfaceAnimationCollection.
        # With the SurfaceAnimationCollection, we can call play() and stop() on
        # all the animation objects at the same time, so that way they'll
        # always be in sync with each other.
        self.surface_animations.add(self.sprite)

    def get_sprites(
        self, layer: int
    ) -> Sequence[Tuple[pygame.surface.Surface, Vector2, int]]:
        """
        Get the surfaces and layers for the sprite.

        Used to render the NPC.

        Parameters:
            layer: The layer to draw the sprite on.

        Returns:
            Tuple containing the surface to plot, the current position
            of the NPC and the layer.

        """

        def get_frame(d: SpriteMap, ani: str) -> pygame.surface.Surface:
            frame = d[ani]
            if isinstance(frame, surfanim.SurfaceAnimation):
                surface = frame.get_current_frame()
                frame.rate = self.moverate / CONFIG.player_walkrate
                return surface
            else:
                return frame

        # TODO: move out to the world renderer
        frame_dict: SpriteMap = self.sprite if self.moving else self.standing
        state = animation_mapping[self.moving][self.facing]
        return [(get_frame(frame_dict, state), proj(self.position3), layer)]

    def pathfind(self, destination: Tuple[int, int]) -> None:
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
            self.path = path
            self.next_waypoint()

    def check_continue(self) -> None:
        try:
            direction_next = self.world.collision_map[self.tile_pos][
                "continue"
            ]
            self.move_one_tile(direction_next)
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

        The tile postion will be truncated, so even if there is another
        closer tile, it will always return the the tile where movement
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
        self.update_physics(time_delta)
        self.surface_animations.update(time_delta)

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
            self.surface_animations.stop()

    def move_one_tile(self, direction: Direction) -> None:
        """
        Ask entity to move one tile.

        Parameters:
            direction: Direction where to move.

        """
        self.path.append(
            vector2_to_tile_pos(Vector2(self.tile_pos) + dirs2[direction])
        )

    def valid_movement(self, tile: Tuple[int, int]) -> bool:
        """
        Check the game map to determine if a tile can be moved into.

        * Only checks adjacent tiles
        * Uses all advanced tile movements, like continue tiles

        Parameters:
            tile: Coordinates of the tile.

        Returns:
            If the tile can me moved into.

        """
        return (
            tile in self.world.get_exits(self.tile_pos)
            or self.ignore_collisions
        )

    @property
    def move_destination(self) -> Optional[Tuple[int, int]]:
        """Only used for the player_moved condition."""
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
        if self.valid_movement(target):
            # surfanim has horrible clock drift.  even after one animation
            # cycle, the time will be off.  drift causes the walking steps to not
            # align with tiles and some frames will only last one game frame.
            # using play to start each tile will reset the surfanim timer
            # and prevent the walking animation frames from coming out of sync.
            # it still occasionally happens though!
            # eventually, there will need to be a global clock for the game,
            # not based on wall time, to prevent visual glitches.
            self.surface_animations.play()
            self.path_origin = self.tile_pos
            self.velocity3 = self.moverate * dirs3[direction]
        else:
            # the target is blocked now
            self.stop_moving()

            if self.pathfinding:
                # since we are pathfinding, just try a new path
                logger.error(f"{self.slug} finding new path!")
                self.pathfind(self.pathfinding)

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
        if self.world.client.isclient or self.world.client.ishost:
            self.world.client.client.update_player(
                direction, event_type="CLIENT_MOVE_START"
            )

    def network_notify_stop_moving(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        if self.world.client.isclient or self.world.client.ishost:
            self.world.client.client.update_player(
                self.facing, event_type="CLIENT_MOVE_COMPLETE"
            )

    def network_notify_location_change(self) -> None:
        r"""WIP guesswork ¯\_(ツ)_/¯"""
        self.update_location = True

    ####################################################
    #                   Monsters                       #
    ####################################################
    def add_monster(self, monster: Monster, slot: int = None) -> None:
        """
        Adds a monster to the npc's list of monsters.

        If the player's party is full, it will send the monster to
        PCState archive.

        Parameters:
            monster: The monster to add to the npc's party.

        """
        monster.owner = self
        if len(self.monsters) >= self.party_limit:
            self.monster_boxes[CONFIG.default_monster_storage_box].append(
                monster
            )
        else:
            if slot is None:
                self.monsters.append(monster)
            else:
                self.monsters.insert(slot, monster)
            self.set_party_status()

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

    def find_monster_in_storage(
        self, instance_id: uuid.UUID
    ) -> Optional[Monster]:
        """
        Finds a monster in the npc's storage boxes which has the given id.

        Parameters:
            instance_id: The insance_id of the monster.

        Returns:
            Monster found, or None.

        """
        monster = None
        for box in self.monster_boxes.values():
            monster = next(
                (m for m in box if m.instance_id == instance_id), None
            )
            if monster is not None:
                break

        return monster

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
            self.set_party_status()
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
            self.set_party_status()

    def evolve_monster(self, old_monster: Monster, evolution: str) -> None:
        """
        Evolve a monster from this npc's party.

        Parameters:
            old_monster: Monster to remove from the npc's party.
            evolution: Monster to add to the npc's party.

        """
        if old_monster not in self.monsters:
            return

        # TODO: implement an evolution animation
        slot = self.monsters.index(old_monster)
        new_monster = Monster()
        new_monster.load_from_db(evolution)
        new_monster.set_level(old_monster.level)
        new_monster.current_hp = min(old_monster.current_hp, new_monster.hp)
        new_monster.moves = old_monster.moves
        new_monster.instance_id = old_monster.instance_id
        new_monster.gender = old_monster.gender
        new_monster.capture = old_monster.capture
        self.remove_monster(old_monster)
        self.add_monster(new_monster, slot)

        # set evolution as caught
        self.tuxepedia[evolution] = SeenStatus.caught

        # If evolution has a flair matching, copy it
        for new_flair in new_monster.flairs.values():
            for old_flair in old_monster.flairs.values():
                if new_flair.category == old_flair.category:
                    new_monster.flairs[new_flair.category] = old_flair

    def remove_monster_from_storage(self, monster: Monster) -> None:
        """
        Removes the monster from the npc's storage.

        Parameters:
            monster: Monster to remove from storage.

        """

        for box in self.monster_boxes.values():
            if monster in box:
                box.remove(monster)
                return

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

    def load_party(self) -> None:
        """Loads the party of this npc from their npc.json entry."""
        for monster in self.monsters:
            self.remove_monster(monster)

        self.monsters = []

        # Look up the NPC's details from our NPC database
        npc_details = db.lookup(self.slug, "npc")
        npc_party = npc_details.monsters
        for npc_monster_details in npc_party:
            # This seems slightly wrong. The only useable element in
            # npc_monsters_details, which is a PartyMemberModel, is "slug"
            monster = Monster(save_data=npc_monster_details.dict())
            monster.money_modifier = npc_monster_details.money_mod
            monster.experience_required_modifier = (
                npc_monster_details.exp_req_mod
            )
            monster.set_level(monster.level)
            monster.current_hp = monster.hp
            monster.gender = npc_monster_details.gender

            # Add our monster to the NPC's party
            self.add_monster(monster)

    def set_party_status(self) -> None:
        """Records important information about all monsters in the party."""
        if not self.isplayer or len(self.monsters) == 0:
            return

        level_lowest = MAX_LEVEL
        level_highest = 0
        level_average = 0
        for npc_monster in self.monsters:
            if npc_monster.level < level_lowest:
                level_lowest = npc_monster.level
            if npc_monster.level > level_highest:
                level_highest = npc_monster.level
            level_average += npc_monster.level
        level_average = int(round(level_average / len(self.monsters)))
        self.game_variables["party_level_lowest"] = level_lowest
        self.game_variables["party_level_highest"] = level_highest
        self.game_variables["party_level_average"] = level_average

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

    def has_type(self, element: ElementType) -> bool:
        """
        Returns TRUE if there is the type in the party.

        Parameters:
            type: The slug name of the type.
        """
        for mon in self.monsters:
            if mon.type1 == element:
                return True
            elif mon.type2 == element:
                return True
        return False

    def give_money(self, amount: int) -> None:
        self.money["player"] += amount

    def has_item(self, item_slug: str) -> bool:
        return self.inventory.get(item_slug) is not None

    def is_item_sort(self, item_slug: str, sort_slug: str) -> bool:
        """
        Is the item sort "sort" (eg. potion, etc.)
        """
        result = db.lookup(item_slug, table="item")
        if result.sort == sort_slug:
            return True
        else:
            return False

    def alter_item_quantity(
        self, session: Session, item_slug: str, amount: int
    ) -> bool:
        success = True
        item = self.inventory.get(item_slug)
        if amount > 0:
            if item:
                item["quantity"] += amount
            else:
                self.inventory[item_slug] = {
                    "item": Item(session, self, item_slug),
                    "quantity": amount,
                }
        elif amount < 0:
            amount = abs(amount)
            if item is None or item.get("infinite"):
                pass
            elif item["quantity"] == amount:
                del self.inventory[item_slug]
            elif item["quantity"] > amount:
                item["quantity"] -= amount
            else:
                success = False

        return success

    def can_buy_item(self, item_slug: str, qty: int, unit_price: int) -> bool:
        current_money = self.money.get("player")
        if current_money is not None:
            return current_money >= qty * unit_price
        # If no 'money' variable, must be an NPC. Always allow buying:
        return True

    def can_sell_item(self, item_slug: str, qty: int, unit_price: int) -> bool:
        current_item = self.inventory.get(item_slug)
        if current_item:
            current_qty = current_item["quantity"]
            return current_qty >= qty or current_item["infinite"]
        # If they don't have the item, then they can't sell the item:
        return False

    def buy_decrease_money(
        self,
        session: Session,
        seller: NPC,
        item_slug: str,
        qty: int,
        unit_price: int,
    ) -> None:
        """
        Decreases player money during a buy transaction.
        """
        # Update player's money.
        if self.money.get("player"):
            if not self.can_buy_item(item_slug, qty, unit_price):
                raise Exception(
                    f"Tried to buy item with {self.money['player']} coins "
                    f"but not enough money:\n"
                    f"price {unit_price} times qty {qty} is {qty * unit_price}"
                )

            # Update player's and NPC money.
            self.money["player"] = self.money.get("player") - (
                qty * unit_price
            )

    def sell_increase_money(
        self,
        session: Session,
        buyer: NPC,
        item_slug: str,
        qty: int,
        unit_price: int,
    ) -> None:
        """
        Increases player money during a sell transaction.
        """
        current_item = self.inventory.get(item_slug)
        if not current_item or not self.can_sell_item(
            item_slug, qty, unit_price
        ):
            raise Exception(
                f"Tried to sell item of qty {qty}, but not enough available."
            )

        # Update player's and NPC money.
        if self.money.get("player") is not None:
            self.money["player"] = self.money.get("player") + (
                qty * unit_price
            )

    def buy_transaction(
        self,
        session: Session,
        seller: NPC,
        item_slug: str,
        qty: int,
        unit_price: int,
    ) -> None:
        """
        Handles the entire buy transaction, NPC (seller) and buyer.
        """
        self.buy_decrease_money(session, seller, item_slug, qty, unit_price)
        self.alter_item_quantity(session, item_slug, qty)
        seller.alter_item_quantity(session, item_slug, -qty)

    def sell_transaction(
        self,
        session: Session,
        seller: NPC,
        item_slug: str,
        qty: int,
        unit_price: int,
    ) -> None:
        """
        Handles the entire sell transaction, NPC (buyer) and seller.
        """
        seller.sell_increase_money(session, self, item_slug, qty, unit_price)
        seller.alter_item_quantity(session, item_slug, -qty)

    def speed_test(self, action: EnqueuedAction) -> int:
        return self.speed
