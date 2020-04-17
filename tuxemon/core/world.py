import logging

from tuxemon.core import prepare
from tuxemon.core.map_loader import TMXMapLoader

logger = logging.getLogger(__name__)


class World(object):
    """

    contains maps, entities, variables, game event handler, and scheduler

    """

    def __init__(self):
        """ Constructor
        """
        self.entities = None
        self.npcs = dict()
        self.maps = dict()
        self.time = 0.0

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
        # for map_object in self.maps.values():
        #     map_object.update(time_delta)
        self.move_npcs(time_delta)

    def add_entity(self, entity):
        """

        :type entity: core.entity.Entity
        :return:
        """
        if entity.map not in self.maps:
            if entity.map_name:
                entity.map = self.get_map(entity.map_name)
        self.npcs[entity.slug] = entity

    def get_entity(self, slug):
        """ Return NPC object by its slug

        :type slug: str
        :return:
        """
        return self.npcs.get(slug)

    def remove_entity(self, slug):
        """ Remove an entity by slug

        :type slug: str
        :return:
        """
        del self.npcs[slug]

    def get_all_entities(self):
        """ List of npcs for collision checking

        :return:
        """
        return self.npcs.values()

    def get_all_entities_on_map(self, map_name):
        """

        :param map_name:
        :return:
        """
        # TODO: filter by map
        return self.npcs.values()

    def move_npcs(self, time_delta):
        """ Move NPCs and Players around according to their state

        :type time_delta: float
        :return:
        """
        for entity in self.get_all_entities():
            entity.move(time_delta)

            # if entity.update_location:
            #     char_dict = {"tile_pos": entity.final_move_dest}
            #     networking.update_client(entity, char_dict, self.game)
            #     entity.update_location = False

    def get_map(self, map_name):
        """ Return a TuxemonMap, loading if it needed

        :param str map_name: Name of map without the filename
        :rtype: TuxemonMap
        """
        map_object = self.maps.get(map_name)
        if map_object is None:
            map_object = self.load_map(map_name)
        return map_object

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

        world.npcs = {}
        for client in registry:
            if "sprite" in registry[client]:
                sprite = registry[client]["sprite"]
                client_map = registry[client]["map_name"]
                # NOTE: get_map_name is broken
                # current_map = self.get_map_name()

                # Add the player to the screen if they are on the same map.
                if client_map == current_map:
                    if sprite.slug not in world.npcs:
                        world.npcs[sprite.slug] = sprite

                # Remove player from the map if they have changed maps.
                elif client_map != current_map:
                    if sprite.slug in world.npcs:
                        del world.npcs[sprite]

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
        for npc in self.npcs.values():
            char_dict = {"tile_pos": npc.tile_pos}
            networking.update_client(npc, char_dict, self.game)
