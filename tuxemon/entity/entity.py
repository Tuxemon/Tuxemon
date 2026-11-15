# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from tuxemon.db import Direction, FacingMode
from tuxemon.map.map import dirs2, tile_distance, vector2_to_tile_pos
from tuxemon.math import Vector2
from tuxemon.save_system.save_state import NPCState
from tuxemon.user_config import CONFIG

if TYPE_CHECKING:
    from tuxemon.network.manager import NetworkManager
    from tuxemon.session import Session


class EntityState(Enum):
    IDLE = "idle"
    WALKING = "walking"
    RUNNING = "running"
    JUMPING = "jumping"


class Body:
    """
    Handles 2D movement of an entity.
    """

    def __init__(
        self,
        position: Vector2,
        velocity: Vector2 | None = None,
        acceleration: Vector2 | None = None,
    ) -> None:
        self.position = position
        self.velocity = velocity or Vector2(0, 0)
        self.acceleration = acceleration or Vector2(0, 0)

    @property
    def is_moving(self) -> bool:
        """Returns whether the entity is currently moving."""
        return self.velocity != Vector2(0, 0)

    def update(self, dt: float) -> None:
        """Updates the position based on velocity and time."""
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

    def reset(
        self,
        reset_position: bool = True,
        reset_velocity: bool = True,
        reset_acceleration: bool = True,
    ) -> None:
        """
        Resets attributes selectively.
        """
        if reset_position:
            self.position = Vector2(0, 0)
        if reset_velocity:
            self.velocity = Vector2(0, 0)
        if reset_acceleration:
            self.acceleration = Vector2(0, 0)


class Mover:
    """
    Handles movement state transitions and movement logic.
    """

    def __init__(
        self,
        body: Body,
        facing: Direction = Direction.DOWN,
        facing_mode: FacingMode = FacingMode.FOLLOW_MOVEMENT,
        base_moverate: float = CONFIG.player_walkrate,
        moverate_modifier: float = 1.0,
    ) -> None:
        self.state = EntityState.IDLE
        self.body = body
        self.facing = facing
        self.facing_mode = facing_mode
        self.base_moverate = base_moverate
        self.moverate_modifier = moverate_modifier
        self.move_direction: Direction | None = None

    @property
    def moverate(self) -> float:
        return self.base_moverate * self.moverate_modifier

    @property
    def is_moving_state(self) -> bool:
        return self.state in (
            EntityState.WALKING,
            EntityState.RUNNING,
            EntityState.JUMPING,
        )

    def move(self, direction: Direction) -> None:
        """Applies movement in a given direction."""
        direction_vector = dirs2[direction]
        self.body.velocity = direction_vector * self.moverate
        if self.facing_mode == FacingMode.FOLLOW_MOVEMENT:
            self.facing = direction

        if self.state == EntityState.IDLE:
            self.set_state(EntityState.WALKING)

    def stop(self) -> None:
        """Stops movement and transitions to IDLE."""
        self.body.velocity = Vector2(0, 0)
        self.set_state(EntityState.IDLE)

    def _set_movement_speed(self, running: bool) -> None:
        """Configure moverate and state for running or walking."""
        self.base_moverate = (
            CONFIG.player_runrate if running else CONFIG.player_walkrate
        )
        new_state = EntityState.RUNNING if running else EntityState.WALKING
        self.set_state(new_state)

    def running(self) -> None:
        """Boosts moverate to running speed."""
        if self.body.is_moving:
            self._set_movement_speed(running=True)

    def walking(self) -> None:
        """Resets moverate back to walking speed."""
        if self.body.is_moving:
            self._set_movement_speed(running=False)

    def jump(self) -> None:
        """Triggers a jump animation state."""
        if self.state != EntityState.JUMPING:
            self.set_state(EntityState.JUMPING)

    def set_state(self, new_state: EntityState) -> None:
        """
        Controls the entity's state transitions.
        """
        if self.state == new_state:
            return

        # Reset movement when going idle
        if new_state == EntityState.IDLE:
            self.body.velocity = Vector2(0, 0)
            self.base_moverate = CONFIG.player_walkrate

        self.state = new_state

    def update_movement_state(self, running: bool) -> None:
        """
        Updates movement state based on whether the player is running
        or walking.
        """
        if self.body.is_moving:
            if running:
                self.running()
            else:
                self.walking()
        else:
            self.stop()

    def has_reached_next_tile(
        self, origin: tuple[int, int], target: tuple[int, int]
    ) -> bool:
        expected = tile_distance(origin, target)
        traveled = tile_distance(self.body.position, origin)
        return traveled >= expected

    def set_moverate(self, moverate: float) -> None:
        """Sets the entity's movement rate."""
        self.base_moverate = moverate

    def set_moverate_modifier(self, modifier: float) -> None:
        """Sets a new moverate modifier."""
        self.moverate_modifier = max(0.0, modifier)

    def set_facing(self, direction: Direction) -> None:
        """Sets the entity's facing direction."""
        self.facing = direction

    def set_facing_mode(self, facing_mode: FacingMode) -> None:
        """Sets the entity's facing mode."""
        self.facing_mode = facing_mode

    def set_move_direction(self, direction: Direction | None = None) -> None:
        """Sets the move direction of the entity."""
        self.move_direction = direction


class Entity:
    """
    Entity in the game.

    Eventually a class for all things that exist on the
    game map, like NPCs, players, objects, etc.

    Need to refactor in most NPC code to here.
    Need to refactor -out- all drawing/sprite code.
    """

    def __init__(
        self,
        *,
        session: Session,
        slug: str = "",
        instance_id: UUID | None = None,
    ):
        self.slug = slug
        self.session = session
        self.client = session.client
        self.event_bus = session.client.event_bus
        self.instance_id = instance_id or uuid4()
        self.body = Body(position=Vector2(0, 0))
        self.mover = Mover(self.body)
        self._current_map: str | None = None
        self.update_location: bool = False
        self.is_player: bool = False
        self.ignore_collisions: bool = False
        self._last_tile_pos = self.tile_pos

    @classmethod
    def create(cls, session: Session, slug: str) -> Entity:
        return cls(session=session, slug=slug)

    @classmethod
    def from_save(cls, session: Session, save_data: NPCState) -> Entity:
        iid = save_data.instance_id
        instance_id = UUID(iid) if iid else None
        entity = cls(session=session, instance_id=instance_id)
        entity.set_state(session, save_data)
        return entity

    # === PHYSICS START =======================================================
    def stop_moving(self) -> None:
        """Completely stop all movement."""
        self.mover.stop()

    def pos_update(self) -> None:
        """WIP.  Required to be called after position changes."""
        self.network_notify_location_change()

    def network_notify_start_moving(self, direction: Direction) -> None:
        if self.network.is_connected():
            assert self.network.client
            self.network.client.update_player(
                direction, event_type="CLIENT_MOVE_START"
            )

    def network_notify_stop_moving(self) -> None:
        if self.network.is_connected():
            assert self.network.client
            self.network.client.update_player(
                self.facing, event_type="CLIENT_MOVE_COMPLETE"
            )

    def network_notify_location_change(self) -> None:
        self.update_location = True

    def update_physics(self, dt: float) -> None:
        """Move the entity according to the movement vector."""
        before_tile = self._last_tile_pos

        self.body.update(dt)

        after_tile = self.tile_pos
        self._last_tile_pos = after_tile

        if after_tile != before_tile:
            dx = after_tile[0] - before_tile[0]
            dy = after_tile[1] - before_tile[1]

            self.event_bus.publish(
                "entity_moved",
                entity=self,
                diff_x=dx,
                diff_y=dy,
                steps=1,
            )

        self.pos_update()

    def set_position(self, pos: Sequence[float]) -> None:
        """Set the entity's position in the game world."""
        self.body.position = Vector2(*pos)
        self.pos_update()

    def on_tile_changed(self) -> None:
        """
        Call this only when the entity enters a new tile
        (path step, teleport, warp, snap-back, spawn).
        Do NOT call from set_position() or physics.
        """
        self.add_collision(self.tile_pos)
        self.pos_update()

    def set_current_map(self, map_slug: str | None) -> None:
        """Set the entity's map in the game world."""
        self._current_map = map_slug

    def set_moverate(self, moverate: float) -> None:
        """Sets the entity's movement rate."""
        self.mover.set_moverate(moverate)

    def set_moverate_modifier(self, modifier: float) -> None:
        """Sets a new moverate modifier."""
        self.mover.set_moverate_modifier(modifier)

    def set_facing(self, direction: Direction) -> None:
        """Sets the entity's facing direction."""
        self.mover.set_facing(direction)

    def set_facing_mode(self, facing_mode: FacingMode) -> None:
        """Sets the entity's facing mode."""
        self.mover.set_facing_mode(facing_mode)

    def set_move_direction(self, direction: Direction | None = None) -> None:
        """Sets the move direction of the entity."""
        self.mover.set_move_direction(direction)

    def add_collision(self, tile_pos: tuple[int, int]) -> None:
        """Set the entity's wandering position in the collision zone."""
        self.client.collision_manager.add_collision(self, tile_pos)

    def remove_collision(self) -> None:
        """Remove the entity's wandering position from the collision zone."""
        self.client.collision_manager.remove_collision(self.tile_pos)

    def begin_tile_exit(self) -> None:
        """Begin transition off current tile by removing collision."""
        self.remove_collision()

    def complete_tile_entry(self, tile_pos: tuple[int, int]) -> None:
        """Complete entry onto a tile, finalizing position and triggering callbacks."""
        self.set_position(tile_pos)
        self.on_tile_changed()

    # === PHYSICS END =========================================================

    @property
    def network(self) -> NetworkManager:
        return self.client.network_manager

    @property
    def tile_pos(self) -> tuple[int, int]:
        """Return the tile position of the entity."""
        return vector2_to_tile_pos(self.body.position)

    @property
    def current_map(self) -> str | None:
        """Return the current map of the entity."""
        return self._current_map

    @property
    def position(self) -> Vector2:
        """Return the current position of the entity."""
        return self.body.position

    @property
    def velocity(self) -> Vector2:
        """Return the current velocity of the entity."""
        return self.body.velocity

    @property
    def moverate(self) -> float:
        """Returns the moverate."""
        return self.mover.moverate

    @property
    def moving(self) -> bool:
        """Return ``True`` if the entity is moving."""
        return self.body.is_moving

    @property
    def facing(self) -> Direction:
        return self.mover.facing

    @property
    def facing_mode(self) -> FacingMode:
        return self.mover.facing_mode

    @property
    def move_direction(self) -> Direction | None:
        """
        Move direction allows other functions to move the entity in a
        controlled way. To move the entity, change the value to one of
        four directions: left, right, up or down. The entity will then
        move one tile in that direction until it is set to None.
        """
        return self.mover.move_direction

    def get_state(self, session: Session) -> NPCState:
        state = NPCState(
            instance_id=self.instance_id.hex,
            position=[self.position.x, self.position.y],
            tile_pos=self.tile_pos,
            facing=self.facing.value,
            current_map=self.current_map,
            is_player=self.is_player,
        )
        return state

    def set_state(self, session: Session, save_data: NPCState) -> None:
        if save_data.position:
            self.set_position(save_data.position)
        elif save_data.tile_pos:
            x, y = save_data.tile_pos
            self.set_position((float(x), float(y)))

        if save_data.facing:
            self.set_facing(Direction(save_data.facing))

        self.set_current_map(save_data.current_map)
        self.is_player = save_data.is_player
        self._last_tile_pos = self.tile_pos
