# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
import uuid
from functools import partial
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
from tuxemon.battle import Battle, decode_battle, encode_battle
from tuxemon.compat import Rect
from tuxemon.db import ElementType, SeenStatus, db
from tuxemon.entity import Entity
from tuxemon.graphics import load_and_scale
from tuxemon.item.item import MAX_TYPES_BAG, Item, decode_items, encode_items
from tuxemon.locale import T
from tuxemon.map import Direction, dirs2, dirs3, facing, get_direction, proj
from tuxemon.math import Vector2
from tuxemon.monster import (
    MAX_LEVEL,
    MAX_MOVES,
    Monster,
    decode_monsters,
    encode_monsters,
)
from tuxemon.prepare import CONFIG
from tuxemon.session import Session
from tuxemon.states.pc import KENNEL, LOCKER
from tuxemon.states.pc_kennel import MAX_BOX
from tuxemon.technique.technique import Technique
from tuxemon.template import Template, decode_template, encode_template
from tuxemon.tools import open_choice_dialog, open_dialog, vector2_to_tile_pos

if TYPE_CHECKING:
    import pygame

    from tuxemon.item.economy import Economy
    from tuxemon.states.combat.combat import EnqueuedAction
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
    battles: Sequence[Mapping[str, Any]]
    tuxepedia: Dict[str, SeenStatus]
    contacts: Dict[str, str]
    money: Dict[str, int]
    template: Sequence[Mapping[str, Any]]
    items: Sequence[Mapping[str, Any]]
    monsters: Sequence[Mapping[str, Any]]
    player_name: str
    monster_boxes: Dict[str, Sequence[Mapping[str, Any]]]
    item_boxes: Dict[str, Sequence[Mapping[str, Any]]]
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
        world: WorldState,
    ) -> None:
        super().__init__(slug=npc_slug, world=world)

        # load initial data from the npc database
        npc_data = db.lookup(npc_slug, table="npc")

        # This is the NPC's name to be used in dialog
        self.name = T.translate(self.slug)

        # general
        self.behavior: Optional[str] = "wander"  # not used for now
        self.game_variables: Dict[str, Any] = {}  # Tracks the game state
        self.battles: List[Battle] = []  # Tracks the battles
        # Tracks Tuxepedia (monster seen or caught)
        self.tuxepedia: Dict[str, SeenStatus] = {}
        self.contacts: Dict[str, str] = {}
        self.money: Dict[str, int] = {}  # Tracks money
        self.interactions: Sequence[
            str
        ] = []  # List of ways player can interact with the Npc
        self.isplayer = False  # used for various tests, idk
        # This is a list of tuxemon the npc has. Do not modify directly
        self.monsters: List[Monster] = []
        # The player's items.
        self.items: List[Item] = []
        self.template: List[Template] = []
        self.economy: Optional[Economy] = None
        # Variables for long-term item and monster storage
        # Keeping these seperate so other code can safely
        # assume that all values are lists
        self.monster_boxes: Dict[str, List[Monster]] = {}
        self.item_boxes: Dict[str, List[Item]] = {}

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
            "battles": encode_battle(self.battles),
            "tuxepedia": self.tuxepedia,
            "contacts": self.contacts,
            "money": self.money,
            "items": encode_items(self.items),
            "template": encode_template(self.template),
            "monsters": encode_monsters(self.monsters),
            "player_name": self.name,
            "monster_boxes": dict(),
            "item_boxes": dict(),
            "tile_pos": self.tile_pos,
        }

        for monsterkey, monstervalue in self.monster_boxes.items():
            state["monster_boxes"][monsterkey] = encode_monsters(monstervalue)

        for itemkey, itemvalue in self.item_boxes.items():
            state["item_boxes"][itemkey] = encode_items(itemvalue)

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
        self.tuxepedia = save_data["tuxepedia"]
        self.contacts = save_data["contacts"]
        self.money = save_data["money"]
        self.battles = []
        for battle in decode_battle(save_data.get("battles")):
            self.battles.append(battle)
        self.items = []
        for item in decode_items(save_data.get("items")):
            self.add_item(item)
        self.monsters = []
        for monster in decode_monsters(save_data.get("monsters")):
            self.add_monster(monster, len(self.monsters))
        self.template = []
        for tmp in decode_template(save_data.get("template")):
            self.template.append(tmp)
        self.name = save_data["player_name"]
        for monsterkey, monstervalue in save_data["monster_boxes"].items():
            self.monster_boxes[monsterkey] = decode_monsters(monstervalue)
        for itemkey, itemvalue in save_data["item_boxes"].items():
            self.item_boxes[itemkey] = decode_items(itemvalue)

        self.load_sprites()

    def load_sprites(self) -> None:
        """Load sprite graphics."""
        # TODO: refactor animations into renderer
        # Get all of the player's standing animation images.
        self.sprite_name = ""
        if not self.template:
            self.sprite_name = "adventurer"
            template = Template()
            template.slug = self.sprite_name
            template.sprite_name = self.sprite_name
            template.combat_front = self.sprite_name
            self.template.append(template)
        else:
            for tmp in self.template:
                self.sprite_name = tmp.sprite_name

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
            self.path = list(path)
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
    def add_monster(self, monster: Monster, slot: int) -> None:
        """
        Adds a monster to the npc's list of monsters.

        If the player's party is full, it will send the monster to
        PCState archive.

        Parameters:
            monster: The monster to add to the npc's party.

        """
        # it creates the kennel
        if KENNEL not in self.monster_boxes.keys():
            self.monster_boxes[KENNEL] = []

        monster.owner = self
        if len(self.monsters) >= self.party_limit:
            self.monster_boxes[KENNEL].append(monster)
            if len(self.monster_boxes[KENNEL]) >= MAX_BOX:
                i = sum(
                    1
                    for ele, mon in self.monster_boxes.items()
                    if ele.startswith(KENNEL) and len(mon) >= MAX_BOX
                )
                self.monster_boxes[f"{KENNEL}{i}"] = self.monster_boxes[KENNEL]
                self.monster_boxes[KENNEL] = []
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
        new_monster.capture_device = old_monster.capture_device
        new_monster.taste_cold = old_monster.taste_cold
        new_monster.taste_warm = old_monster.taste_warm
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
            monster.experience_modifier = npc_monster_details.exp_req_mod
            monster.set_level(monster.level)
            monster.set_moves(monster.level)
            monster.current_hp = monster.hp
            monster.gender = npc_monster_details.gender

            # Add our monster to the NPC's party
            self.add_monster(monster, len(npc_party))

        # load NPC bag
        for item in self.items:
            self.remove_item(item)
        self.items = []
        npc_bag = npc_details.items
        for npc_itm_details in npc_bag:
            itm = Item(save_data=npc_itm_details.dict())
            itm.quantity = npc_itm_details.quantity

        # load NPC template
        for tmp in self.template:
            self.template.remove(tmp)
        self.template = []
        npc_template = npc_details.template
        for npc_template_details in npc_template:
            tmp = Template(save_data=npc_template_details.dict())
            tmp.sprite_name = npc_template_details.sprite_name
            tmp.combat_front = npc_template_details.combat_front
            self.template.append(tmp)

        self.load_sprites()

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

    def has_type(self, element: Optional[ElementType]) -> bool:
        """
        Returns TRUE if there is the type in the party.

        Parameters:
            type: The slug name of the type.
        """
        for mon in self.monsters:
            if element in mon.types:
                return True
            else:
                return False
        return False

    def check_max_moves(self, session: Session, monster: Monster) -> None:
        """
        Checks the number of moves:
        if monster has >= 4 moves (MAX_MOVES) -> overwrite technique
        if monster has < 4 moves (MAX_MOVES) -> learn technique
        """
        overwrite_technique = session.player.game_variables[
            "overwrite_technique"
        ]

        if len(monster.moves) >= MAX_MOVES:
            self.overwrite_technique(session, monster, overwrite_technique)
        else:
            overwrite = Technique()
            overwrite.load(overwrite_technique)
            monster.learn(overwrite)
            msg = T.translate("generic_success")
            open_dialog(session, [msg])

    def overwrite_technique(
        self, session: Session, monster: Monster, technique: str
    ) -> None:
        """
        Opens the choice dialog and overwrites the technique.
        """
        tech = Technique()
        tech.load(technique)

        def set_variable(var_value: Technique) -> None:
            monster.moves.remove(var_value)
            monster.learn(tech)
            session.client.pop_state()

        var_list = monster.moves
        var_menu = list()

        for val in var_list:
            text = T.translate(val.slug)
            var_menu.append((text, text, partial(set_variable, val)))

        open_choice_dialog(
            session,
            menu=var_menu,
        )
        open_dialog(
            session,
            [
                T.format(
                    "max_moves_alert",
                    {
                        "name": monster.name.upper(),
                        "tech": tech.name,
                    },
                )
            ],
        )

    def remove_technique(
        self,
        session: Session,
        monster: Monster,
    ) -> None:
        """
        Opens the choice dialog and removes the technique.
        """

        def set_variable(var_value: Technique) -> None:
            monster.moves.remove(var_value)
            session.client.pop_state()

        var_list = monster.moves
        var_menu = list()

        for val in var_list:
            text = T.translate(val.slug)
            var_menu.append((text, text, partial(set_variable, val)))

        open_choice_dialog(
            session,
            menu=var_menu,
        )
        open_dialog(
            session,
            [
                T.format(
                    "new_tech_delete",
                    {
                        "name": monster.name.upper(),
                    },
                )
            ],
        )

    ####################################################
    #                      Items                       #
    ####################################################
    def add_item(self, item: Item) -> None:
        """
        Adds an item to the npc's bag.

        If the player's bag is full, it will send the item to
        PCState archive.

        """
        # it creates the locker
        if LOCKER not in self.item_boxes.keys():
            self.item_boxes[LOCKER] = []

        if len(self.items) >= MAX_TYPES_BAG:
            self.item_boxes[LOCKER].append(item)
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

    def find_item_in_storage(self, instance_id: uuid.UUID) -> Optional[Item]:
        """
        Finds an item in the npc's storage boxes which has the given id.

        """
        item = None
        for box in self.item_boxes.values():
            item = next((m for m in box if m.instance_id == instance_id), None)
            if item is not None:
                break

        return item

    def remove_item_from_storage(self, item: Item) -> None:
        """
        Removes the item from the npc's storage.

        """
        for box in self.item_boxes.values():
            if item in box:
                box.remove(item)
                return

    def give_money(self, amount: int) -> None:
        self.money["player"] += amount

    def speed_test(self, action: EnqueuedAction) -> int:
        return self.speed
