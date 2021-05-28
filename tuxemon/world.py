import logging
from collections import defaultdict
from typing import Optional, List

from tuxemon import prepare
from tuxemon.clock import Scheduler
from tuxemon.constants import paths
from tuxemon.entity import Entity
from tuxemon.lib.euclid import Point2
from tuxemon.event.eventengine import EventEngine
from tuxemon.map import TuxemonMap
from tuxemon.map_loader import TMXMapLoader
from tuxemon.npc import NPC
from tuxemon.plugin import load_plugins

logger = logging.getLogger(__name__)


class Position:
    """

    This represents the position of any game entity, including NPCs and Players

    x = left-right
    y = up-down
    z = height from the ground
    map_name = string name of the map they reside on

    x, y, z values are fractional values representing the tile they are on,
    and are relative to the top-left corner of the map they are on.  There
    is no unified coordinate system across maps.

    Currently, z axis is unused.
    """

    def __init__(self, x, y, z, map_name):
        self.x = x
        self.y = y
        self.z = z
        self.map_name = map_name

    def __getitem__(self, index):
        return (self.x, self.y, self.z)[index]


def proj(point):
    """Project 3d coordinates to 2d.

    :param Union[Point2, Tuple] point:
    :rtype: Tuple[Float, Float]
    """
    try:
        return Point2(point.x, point.y)
    except AttributeError:
        return point[0], point[1]


class World:
    """

    contains maps, entities, clock, scheduler, and eventengine

    """

    def __init__(self):
        """Constructor"""
        self.entities_by_slug = dict()
        self.entities_by_map = defaultdict(set)
        self.maps = dict()
        self.time = 0.0
        self.clock = Scheduler()
        self.eventengine = EventEngine(
            actions=load_plugins(paths.ACTIONS_PATH),
            conditions=load_plugins(paths.CONDITIONS_PATH),
        )

    def teleport(self, npc: NPC, position: Position):
        """Used to instantly move NPC to a new position or map

        Do not abuse this for small movements.
        """
        npc.abort_movement()
        self.remove_entity(npc.slug)
        self.add_entity(npc, position)

    def update(self, time_delta: float):
        """Update time"""
        self.clock.tick()
        self.eventengine.update(time_delta)

    def add_entity(self, entity: Entity, position: Position):
        """Add entity to world with a position"""
        entity.set_position(position)
        if position.map_name not in self.maps:
            entity.map = self.get_map(position.map_name)
        self.entities_by_slug[entity.slug] = entity
        self.entities_by_map[position.map_name].add(entity)

    def remove_entity(self, slug: str):
        """Remove an entity by its slug"""
        entity = self.entities_by_slug[slug]
        del self.entities_by_slug[slug]
        for map_name, entities in self.entities_by_map.items():
            try:
                entities.remove(entity)
            except KeyError:
                pass
            else:
                break

    def clear_entities_on_map(self, map_name):
        for entity in self.entities_by_slug[map_name]:
            self.remove_entity(entity.slug)
        del self.entities_by_map[map_name]

    def get_entity(self, slug: str) -> Optional[Entity]:
        """Return Entity by its slug.  Returns None if not found"""
        return self.entities_by_slug.get(slug)

    def get_all_entities(self) -> List[Entity]:
        """All entities across all maps"""
        return list(self.entities_by_slug.values())

    def get_entities_on_map(self, map_name: str) -> List[Entity]:
        """All entities on a map"""
        if map_name not in self.entities_by_map:
            raise Exception
        return list(self.entities_by_map[map_name])

    def get_map_for_entity(self, entity) -> TuxemonMap:
        for name, map_object in self.entities_by_map.items():
            if entity in map_object:
                return self.maps[name]
        raise RuntimeError

    def load_map(self, map_name: str) -> TuxemonMap:
        """Load a map from disk and cache it

        * If the map is already loaded, it will be cleared!
        """
        filename = prepare.fetch("maps", map_name)
        map_object = TMXMapLoader().load(filename)
        self.maps[map_name] = map_object
        self.eventengine.load_events(map_object.events)
        return map_object

    def get_map(self, map_name: str) -> TuxemonMap:
        """Return a TuxemonMap, loading if it needed"""
        map_object = self.maps.get(map_name)
        if map_object is None:
            return self.load_map(map_name)
        return map_object

    def unload_map(self, map_name):
        self.clear_entities_on_map(map_name)
        # TODO: unload map events
        del self.maps[map_name]
