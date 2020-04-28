import logging
from collections import defaultdict

from tuxemon.compat import Rect
from tuxemon.core import prepare
from tuxemon.core.euclid import Vector3, Point2
from tuxemon.core.map_loader import TMXMapLoader

logger = logging.getLogger(__name__)


def proj(point):
    """ Project 3d coordinates to 2d.

    :param Union[Point2, Tuple] point:
    :rtype: Tuple[Float, Float]
    """
    try:
        return Point2(point.x, point.y)
    except AttributeError:
        return point[0], point[1]


class WorldBody(object):
    """ WIP Physics for map/world objects
    """

    def __init__(self):
        self.acceleration3 = Vector3(0, 0, 0)
        self.velocity3 = Vector3(0, 0, 0)
        self.position3 = Vector3(0, 0, 0)
        self.bbox2 = Rect(0, 0, 0, 0)
        self.map_name = None

    def stop_moving(self):
        """ Completely stop all movement

        :return: None
        """
        self.acceleration3.x = 0
        self.acceleration3.y = 0
        self.acceleration3.z = 0
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def pos_update(self):
        """ Required to be called after position changes

        :return: None
        """
        self.tile_pos = proj(self.position3)

    def update_physics(self, td):
        """ Move the entity according to the movement vector

        NOTE: gravity, acceleration, friction is not implemented

        :param float td:
        :rtype: None
        """
        self.position3 += self.velocity3 * td
        self.pos_update()

    def set_position(self, pos):
        """ Set the entity's position in the game world

        :param pos:
        :return:
        """
        self.stop_moving()
        self.position3.x = pos[0]
        self.position3.y = pos[1]
        self.pos_update()

    @property
    def moving(self):
        """ Is the body moving?

        :rtype: bool
        """
        return not self.velocity3 == (0, 0, 0)


class World(object):
    """

    contains maps and entities

    """

    def __init__(self):
        """ Constructor
        """
        self.entities = None
        self.npcs_by_slug = dict()
        self.npcs_by_map = defaultdict(set)
        self.maps = dict()
        self.time = 0.0

    def teleport(self, npc, map_name, position):
        """ Used to instantly move NPC to a new position or map

        Do not abuse this for small movements.

        :param tuxemon.core.npc.NPC npc:
        :param str map_name:
        :param Vector3 position: position where to teleport
        :return:
        """
        npc.abort_movement()
        npc.map_name = map_name
        npc.map = self.get_map(map_name)
        npc.set_position(position)
        self.remove_entity(npc.slug)
        self.add_entity(npc)

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
        self.move_npcs(time_delta)
        for map_object in list(self.maps.values()):
            map_object.update(time_delta)

    def add_entity(self, entity):
        """

        :type entity: core.entity.Entity
        :return:
        """
        if entity.body.map_name not in self.maps:
            entity.body.map = self.get_map(entity.map_name)
        self.npcs_by_slug[entity.slug] = entity
        self.npcs_by_map[entity.map_name].add(entity)

    def remove_entity(self, slug):
        """ Remove an entity by its slug

        :type slug: str
        :return:
        """
        entity = self.npcs_by_slug[slug]
        del self.npcs_by_slug[slug]
        for map_name, entities in self.npcs_by_map.items():
            try:
                entities.remove(entity)
            except KeyError:
                pass
            else:
                break

    def clear_entities_on_map(self, map_name):
        for entity in self.npcs_by_slug[map_name]:
            self.remove_entity(entity.slug)
        del self.npcs_by_map[map_name]

    def get_entity(self, slug):
        """ Return NPC object by its slug

        :type slug: str
        :rtype: tuxemon.core.entity.Entity
        """
        return self.npcs_by_slug.get(slug)

    def get_all_entities(self):
        """ All entities across all maps

        :rtype: Iterator[Entity]
        """
        return self.npcs_by_slug.values()

    def get_entities_on_map(self, map_name):
        """ All entities on a map

        :param str map_name:
        :rtype: Iterator[Entity]
        """
        return self.npcs_by_map[map_name]

    def move_npcs(self, time_delta):
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

        world.npcs_by_slug = {}
        for client in registry:
            if "sprite" in registry[client]:
                sprite = registry[client]["sprite"]
                client_map = registry[client]["map_name"]
                # NOTE: get_map_name is broken
                # current_map = self.get_map_name()

                # Add the player to the screen if they are on the same map.
                if client_map == current_map:
                    if sprite.slug not in world.npcs_by_slug:
                        world.npcs_by_slug[sprite.slug] = sprite

                # Remove player from the map if they have changed maps.
                elif client_map != current_map:
                    if sprite.slug in world.npcs_by_slug:
                        del world.npcs_by_slug[sprite]

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
        for npc in self.npcs_by_slug.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.game)
