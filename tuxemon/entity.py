# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from tuxemon.db import Direction
from tuxemon.map import dirs3, proj
from tuxemon.math import Point3, Vector3
from tuxemon.prepare import CONFIG
from tuxemon.session import Session
from tuxemon.tools import vector2_to_tile_pos

if TYPE_CHECKING:
    from tuxemon.states.world.worldstate import WorldState


SaveDict = TypeVar("SaveDict", bound=Mapping[str, Any])


class EntityState(Enum):
    IDLE = "idle"
    WALKING = "walking"
    RUNNING = "running"


class Body:
    """
    Handles physics-related attributes and movement of an entity.
    """

    def __init__(
        self,
        position: Point3,
        velocity: Optional[Vector3] = None,
        acceleration: Optional[Vector3] = None,
    ) -> None:
        self.position = position
        self.velocity = velocity or Vector3(0, 0, 0)
        self.acceleration = acceleration or Vector3(0, 0, 0)

    @property
    def acceleration_magnitude(self) -> float:
        """
        Returns the magnitude of the acceleration vector.
        """
        return self.acceleration.magnitude

    def update(self, time_delta: float) -> None:
        """
        Updates the position based on velocity and time.
        """
        self.velocity += self.acceleration * time_delta
        self.position += self.velocity * time_delta

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
            self.position = Point3(0, 0, 0)
        if reset_velocity:
            self.velocity = Vector3(0, 0, 0)
        if reset_acceleration:
            self.acceleration = Vector3(0, 0, 0)


class Mover:
    def __init__(
        self,
        body: Body,
        facing: Direction = Direction.down,
        moverate: float = 0.0,
    ) -> None:
        self.state = EntityState.IDLE
        self.body = body
        self.facing = facing
        self.moverate = moverate  # walk by default
        self.direction_map = {tuple(v.normalized): k for k, v in dirs3.items()}

    @property
    def current_direction(self) -> Vector3:
        return dirs3[self.facing]

    def move(self, direction: Vector3, speed: float) -> None:
        """Applies movement in a given direction."""
        normalized_direction = tuple(direction.normalized)
        if normalized_direction in self.direction_map:
            self.body.velocity = Vector3(*normalized_direction) * speed
            self.facing = self.direction_map[normalized_direction]
            self.state = (
                EntityState.RUNNING
                if speed > CONFIG.player_walkrate
                else EntityState.WALKING
            )
        else:
            raise ValueError("Invalid direction")

    def stop(self) -> None:
        """Stops movement without affecting acceleration."""
        self.body.velocity = Vector3(0, 0, 0)
        self.state = EntityState.IDLE

    def running(self) -> None:
        """Boosts moverate to running speed."""
        if self.body.velocity != Vector3(0, 0, 0):
            self.moverate = CONFIG.player_runrate
            self.state = EntityState.RUNNING

    def walking(self) -> None:
        """Resets moverate back to walking speed."""
        if self.body.velocity != Vector3(0, 0, 0):
            self.moverate = CONFIG.player_walkrate
            self.state = EntityState.WALKING


class Entity(Generic[SaveDict]):
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
        slug: str = "",
        world: WorldState,
    ) -> None:
        self.slug = slug
        self.world = world
        self.instance_id = uuid.uuid4()
        self.body = Body(position=Point3(0, 0, 0))
        self.mover = Mover(self.body, moverate=CONFIG.player_walkrate)
        self.tile_pos = (0, 0)
        self.update_location = False
        self.isplayer: bool = False

    # === PHYSICS START =======================================================
    def stop_moving(self) -> None:
        """Completely stop all movement."""
        self.mover.stop()

    def pos_update(self) -> None:
        """WIP.  Required to be called after position changes."""
        self.tile_pos = vector2_to_tile_pos(proj(self.body.position))

    def update_physics(self, td: float) -> None:
        """
        Move the entity according to the movement vector.

        Parameters:
            td: Time delta (elapsed time).
        """
        self.body.update(td)
        self.pos_update()

    def set_position(self, pos: Sequence[float]) -> None:
        """
        Set the entity's position in the game world.

        Parameters:
            pos: Position to be set.
        """
        self.body.position = Point3(*pos)
        self.add_collision(pos)
        self.pos_update()

    def set_moverate(self, moverate: float) -> None:
        """
        Sets the entity's movement rate.

        Parameters:
            moverate: The new movement rate to be applied.
        """
        self.mover.moverate = moverate

    def set_facing(self, direction: Direction) -> None:
        """
        Sets the entity's facing direction.

        Parameters:
            direction: The new direction the entity will face.
        """
        self.mover.facing = direction

    def add_collision(self, pos: Sequence[float]) -> None:
        """
        Set the entity's wandering position in the collision zone.
        """
        self.world.add_collision(self, pos)

    def remove_collision(self) -> None:
        """
        Remove the entity's wandering position from the collision zone.
        """
        self.world.remove_collision(self.tile_pos)

    # === PHYSICS END =========================================================

    @property
    def position(self) -> Point3:
        """Return the current position of the entity."""
        return self.body.position

    @property
    def velocity(self) -> Vector3:
        """Return the current velocity of the entity."""
        return self.body.velocity

    @property
    def moverate(self) -> float:
        """Returns the moverate."""
        return self.mover.moverate

    @property
    def moving(self) -> bool:
        """Return ``True`` if the entity is moving."""
        return self.body.velocity != Vector3(0, 0, 0)

    @property
    def facing(self) -> Direction:
        return self.mover.facing

    def get_state(self, session: Session) -> SaveDict:
        """
        Get Entities internal state for saving/loading.

        Parameters:
            session: Game session.
        """
        raise NotImplementedError

    def set_state(
        self,
        session: Session,
        save_data: SaveDict,
    ) -> None:
        """
        Recreates entity from saved data.

        Parameters:
            session: Game session.
            save_data: Data used to recreate the Entity.
        """
        raise NotImplementedError
