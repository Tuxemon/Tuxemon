import logging
from collections import defaultdict

from tuxemon.core import prepare
from tuxemon.core.euclid import Point2
from tuxemon.core.map import TuxemonMap
from tuxemon.core.map_loader import TMXMapLoader

logger = logging.getLogger(__name__)


class Position:
    def __init__(self, x, y, z, map_name):
        self.x = x
        self.y = y
        self.z = z
        self.map_name = map_name

    def __getitem__(self, index):
        return (self.x, self.y, self.z)[index]


def proj(point):
    """ Project 3d coordinates to 2d.

    :param Union[Point2, Tuple] point:
    :rtype: Tuple[Float, Float]
    """
    try:
        return Point2(point.x, point.y)
    except AttributeError:
        return point[0], point[1]


class World(object):
    """

    contains maps and entities

    """

    def __init__(self):
        """ Constructor
        """
        self.entities = None
        self.entities_by_slug = dict()
        self.entities_by_map = defaultdict(set)
        self.maps = dict()
        self.time = 0.0

    def teleport(self, npc, position):
        """ Used to instantly move NPC to a new position or map

        Do not abuse this for small movements.

        :param tuxemon.core.npc.NPC npc:
        :param tuxemon.core.world.Position position:
        :return:
        """
        npc.abort_movement()
        self.remove_entity(npc.slug)
        self.add_entity(npc, position)

    def process_platform_event(self, platform_event):
        """ Handle platform events such as key presses

        :param platform_event:
        :return:
        """
        # TODO: iterate over loaded maps and process events
        # self.event_engine.process_event(platform_event)
        pass

    def update(self, time_delta):
        """ Update time

        :param float time_delta: Time passed since last frame
        :return: None
        """
        self.time += time_delta
        self.move_entities(time_delta)
        for map_object in list(self.maps.values()):
            map_object.update(time_delta)

    def add_entity(self, entity, position):
        """

        :type entity: core.entity.Entity
        :type position: core.world.Position
        :return:
        """
        entity.set_position(position)
        if position.map_name not in self.maps:
            entity.map = self.get_map(position.map_name)
        self.entities_by_slug[entity.slug] = entity
        self.entities_by_map[position.map_name].add(entity)

    def remove_entity(self, slug):
        """ Remove an entity by its slug

        :type slug: str
        :return:
        """
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

    def get_entity(self, slug):
        """ Return Entity by its slug.  Returns None if not found.

        :type slug: str
        :rtype: Optional[tuxemon.core.entity.Entity]
        """
        return self.entities_by_slug.get(slug)

    def get_all_entities(self):
        """ All entities across all maps

        :rtype: Iterator[Entity]
        """
        return self.entities_by_slug.values()

    def get_entities_on_map(self, map_name):
        """ All entities on a map

        :param str map_name:
        :rtype: Iterator[Entity]
        """
        if map_name not in self.entities_by_map:
            raise Exception
        return self.entities_by_map[map_name]

    def get_map_for_entity(self, entity) -> TuxemonMap:
        for name, gamemap in self.entities_by_map.items():
            if entity in gamemap:
                return self.maps[name]
        raise RuntimeError

    def move_entities(self, time_delta):
        """ Move NPCs and Players around according to their state

        :type time_delta: float
        :return:
        """
        for entity in self.get_all_entities():
            entity.move(time_delta)

    def load_map(self, map_name):
        """ Load a map from disk and cache it

        * If the map is already loaded, it will be cleared!

        :param str map_name: Filename without path of the map
        :rtype: TuxemonMap
        """
        filename = prepare.fetch("maps", map_name)
        map_object = TMXMapLoader().load(filename)
        self.maps[map_name] = map_object
        return map_object

    def get_map(self, map_name):
        """ Return a TuxemonMap, loading if it needed

        :param str map_name: Name of map without the filename
        :rtype: TuxemonMap
        """
        map_object = self.maps.get(map_name)
        if map_object is None:
            map_object = self.load_map(map_name)
        return map_object

    def unload_map(self, map_name):
        self.clear_entities_on_map(map_name)
        del self.maps[map_name]

    def add_clients_to_map(self, registry):
        """Checks to see if clients are supposed to be displayed on the current map. If
        they are on the same map as the host then it will add them to the npc's list.
        If they are still being displayed and have left the map it will remove them from
        the map.

        :param registry: Locally hosted Neteria client/server registry.

        :type registry: Dictionary

        :rtype: None
        :returns: None

        """
        raise NotImplementedError("get_map_name is broken")

        world = self.get_state_by_name("WorldState")
        if not world:
            return

        world.entities_by_slug = {}
        for client in registry:
            if "sprite" in registry[client]:
                sprite = registry[client]["sprite"]
                client_map = registry[client]["map_name"]
                # NOTE: get_map_name is broken
                # current_map = self.get_map_name()

                # Add the player to the screen if they are on the same map.
                if client_map == current_map:
                    if sprite.slug not in world.entities_by_slug:
                        world.entities_by_slug[sprite.slug] = sprite

                # Remove player from the map if they have changed maps.
                elif client_map != current_map:
                    if sprite.slug in world.entities_by_slug:
                        del world.entities_by_slug[sprite]

    def broadcast_player_teleport_change(self):
        """ Tell clients/host that player has moved or changed map after teleport
        """
        raise NotImplementedError("npc positions now include map name")

        # Set the transition variable in event_data to false when we're done
        self.game.event_data["transition"] = False

        # Update the server/clients of our new map and populate any other players.
        if self.game.isclient or self.game.ishost:
            self.game.add_clients_to_map(self.game.client.client.registry)
            self.game.client.update_player(self.player1.facing)

        # Update the location of the npcs. Doesn't send network data.
        for npc in self.entities_by_slug.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.game)
