# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from tuxemon.db import Direction
from tuxemon.map import RegionProperties, dirs3, proj
from tuxemon.math import Point3, Vector3
from tuxemon.prepare import CONFIG
from tuxemon.session import Session
from tuxemon.tools import vector2_to_tile_pos

if TYPE_CHECKING:
    from tuxemon.states.world.worldstate import WorldState


SaveDict = TypeVar("SaveDict", bound=Mapping[str, Any])


class Body:
    """
    Handles physics-related attributes and movement of an entity.
    """

    def __init__(
        self,
        position: Point3,
        velocity: Optional[Vector3] = None,
        acceleration: Optional[Vector3] = None,
        facing: Direction = Direction.down,
        moverate: float = 0.0,
    ) -> None:
        self.position = position
        self.velocity = velocity or Vector3(0, 0, 0)
        self.acceleration = acceleration or Vector3(0, 0, 0)
        self.facing = facing
        self.moverate = moverate  # walk by default

    @property
    def acceleration_magnitude(self) -> float:
        """
        Returns the magnitude of the acceleration vector.
        """
        return self.acceleration.magnitude

    @property
    def current_direction(self) -> Vector3:
        return dirs3[self.facing]

    def update(self, time_delta: float) -> None:
        """
        Updates the position based on velocity and time.
        """
        if self.velocity.magnitude > 0:
            self.facing = self._get_facing_from_velocity()
        self.velocity += self.acceleration * time_delta
        self.position += self.velocity * time_delta

    def stop(self) -> None:
        """
        Stops all movement by resetting the velocity to zero.
        """
        self.velocity = Vector3(0, 0, 0)

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

    def _get_facing_from_velocity(self) -> Direction:
        for direction, vector in dirs3.items():
            if vector.normalized == self.velocity.normalized:
                return direction
        return self.facing


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
        world.add_entity(self)
        self.instance_id = uuid.uuid4()
        self.body = Body(
            position=Point3(0, 0, 0), moverate=CONFIG.player_walkrate
        )
        self.tile_pos = (0, 0)
        self.update_location = False
        self.isplayer: bool = False

    # === PHYSICS START =======================================================
    def stop_moving(self) -> None:
        """
        Completely stop all movement.
        """
        self.body.stop()

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

    def add_collision(self, pos: Sequence[float]) -> None:
        """
        Set the entity's wandering position in the collision zone.

        Parameters:
            pos: Position to be added.
        """
        coords = (int(pos[0]), int(pos[1]))
        region = self.world.collision_map.get(coords)

        enter_from = region.enter_from if self.isplayer and region else []
        exit_from = region.exit_from if self.isplayer and region else []
        endure = region.endure if self.isplayer and region else []
        key = region.key if self.isplayer and region else None

        prop = RegionProperties(
            enter_from=enter_from,
            exit_from=exit_from,
            endure=endure,
            entity=self,
            key=key,
        )

        self.world.collision_map[coords] = prop

    def remove_collision(self) -> None:
        """
        Remove the entity's wandering position from the collision zone.
        """
        region = self.world.collision_map.get(self.tile_pos)
        if not region:
            return  # Nothing to remove

        if any([region.enter_from, region.exit_from, region.endure]):
            prop = RegionProperties(
                region.enter_from,
                region.exit_from,
                region.endure,
                None,
                region.key,
            )
            self.world.collision_map[self.tile_pos] = prop
        else:
            # Remove region
            del self.world.collision_map[self.tile_pos]

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
        return self.body.moverate

    @property
    def moving(self) -> bool:
        """Return ``True`` if the entity is moving."""
        return self.body.velocity != Vector3(0, 0, 0)

    @property
    def facing(self) -> Direction:
        return self.body.facing

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
            ave_data: Data used to recreate the Entity.

        """
        raise NotImplementedError
