# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from tuxemon.map import RegionProperties, proj
from tuxemon.math import Point3, Vector3
from tuxemon.session import Session
from tuxemon.tools import vector2_to_tile_pos

if TYPE_CHECKING:
    from tuxemon.states.world.worldstate import WorldState


SaveDict = TypeVar("SaveDict", bound=Mapping[str, Any])


class Entity(Generic[SaveDict]):
    """
    Entity in the game.

    Eventually a class for all things that exist on the
    game map, like NPCs, players, objects, etc.

    Need to refactor in most NPC code to here.
    Need to refactor -out- all drawing/sprite code.
    Consider to refactor out world position/movement into "Body" class.

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
        self.tile_pos = (0, 0)
        self.position3 = Point3(0, 0, 0)
        # not used currently
        self.acceleration3 = Vector3(0, 0, 0)
        self.velocity3 = Vector3(0, 0, 0)
        self.update_location = False

    # === PHYSICS START =======================================================
    def stop_moving(self) -> None:
        """
        Completely stop all movement.

        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def pos_update(self) -> None:
        """WIP.  Required to be called after position changes."""
        self.tile_pos = vector2_to_tile_pos(proj(self.position3))

    def update_physics(self, td: float) -> None:
        """
        Move the entity according to the movement vector.

        Parameters:
            td: Time delta (elapsed time).

        """
        self.position3 += self.velocity3 * td
        self.pos_update()

    def set_position(self, pos: Sequence[float]) -> None:
        """
        Set the entity's position in the game world.

        Parameters:
            pos: Position to be set.

        """
        self.position3.x = pos[0]
        self.position3.y = pos[1]
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
        if region:
            prop = RegionProperties(
                region.enter_from,
                region.exit_from,
                region.endure,
                self,
                region.key,
            )
        else:
            prop = RegionProperties(
                enter_from=[], exit_from=[], endure=[], entity=self, key=None
            )
        self.world.collision_map[coords] = prop

    def remove_collision(self, pos: tuple[int, int]) -> None:
        """
        Remove the entity's wandering position from the collision zone.

        Parameters:
            pos: Position to be removed.

        """
        region = self.world.collision_map.get(pos)
        if region and (region.enter_from or region.exit_from or region.endure):
            prop = RegionProperties(
                region.enter_from,
                region.exit_from,
                region.endure,
                None,
                region.key,
            )
            self.world.collision_map[pos] = prop
        else:
            try:
                del self.world.collision_map[pos]
            except:
                pass

    # === PHYSICS END =========================================================

    @property
    def moving(self) -> bool:
        """Return ``True`` if the entity is moving."""
        return not self.velocity3 == (0, 0, 0)

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
