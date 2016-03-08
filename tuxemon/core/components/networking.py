#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Derek Clark <derekjohn.clark@gmail.com>
#
# core.components.networking
#
"""This module contains the Tuxemon server and client.
"""
from core.components.middleware import Multiplayer, Controller
from core import prepare

from datetime import datetime

import pprint
import pygame as pg

# Create a logger for optional handling of debug messages.
import logging
logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

try:
    from neteria.server import NeteriaServer
    from neteria.client import NeteriaClient
    networking = True
except ImportError:
    logger.info("Neteria networking unavailable")
    networking = False


class TuxemonServer():
    """Server class for multiplayer games. Creates a netaria server and
    synchronizes the local game with all client states.

    :param game: instance of the local game.

    :type game: core.control.Control object.

    :rtype: None
    :returns: None

    """

    def __init__(self, game, server_name=None):

        self.game = game
        if not server_name:
            self.server_name = "Default Tuxemon Server"
        else:
            self.server_name = server_name
        self.network_events = []
        self.listening = False
        self.interfaces = {}
        self.ips = []

        # Handle users without networking support.
        if not networking:
            self.server = DummyNetworking()
            return

        self.server = NeteriaServer(Multiplayer(self), server_port=40081, server_name=self.server_name)


    def update(self):
        """Updates the server state with information sent from the clients

        :param None

        :type None

        :rtype: None
        :returns: None

        """
        self.server_timestamp = datetime.now()
        for cuuid in self.server.registry:
            try:
                difference = self.server_timestamp - self.server.registry[cuuid]["ping_timestamp"]
                if difference.seconds > 15:
                    logger.info("Client Disconnected. CUUID: " + str(cuuid))
                    event_data = {"type": "CLIENT_DISCONNECTED"}
                    self.notify_client(cuuid, event_data)
                    del self.server.registry[cuuid]
                    return False

            except KeyError:
                self.server.registry[cuuid]["ping_timestamp"] = datetime.now()




    def server_event_handler(self, cuuid, event_data):
        """Handles events sent from the middleware that are legal.

        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.

        :type cuuid: String
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        # Only respond to the latest message of a given type
        if not "event_list" in self.server.registry[cuuid]:
            self.server.registry[cuuid]["event_list"] = {}
        elif not event_data["type"] in self.server.registry[cuuid]["event_list"]:
                self.server.registry[cuuid]["event_list"][event_data["type"]] = -1

        elif event_data["event_number"] <= self.server.registry[cuuid]["event_list"][event_data["type"]]:
            return False
        else:
            self.server.registry[cuuid]["event_list"][event_data["type"]] = event_data["event_number"]

        if event_data["type"] == "PUSH_SELF":
            self.server.registry[cuuid]["sprite_name"] = event_data["sprite_name"]
            self.server.registry[cuuid]["map_name"] = event_data["map_name"]
            self.server.registry[cuuid]["char_dict"] = event_data["char_dict"]
            self.server.registry[cuuid]["ping_timestamp"] = datetime.now()
            self.notify_populate_client(cuuid, event_data)

        elif event_data["type"] == "PING":
            self.server.registry[cuuid]["ping_timestamp"] = datetime.now()

        elif event_data["type"] == "CLIENT_INTERACTION" or event_data["type"] == "CLIENT_RESPONSE":
            self.notify_client_interaction(cuuid, event_data)

        elif event_data["type"] == "CLIENT_KEYDOWN":
            if event_data["kb_key"] == "SHIFT":
                self.server.registry[cuuid]["char_dict"]["running"] = True
                self.notify_client(cuuid, event_data)
            elif event_data["kb_key"] == "CTRL":
                self.notify_client(cuuid, event_data)
            elif event_data["kb_key"] == "ALT":
                self.notify_client(cuuid, event_data)

        elif event_data["type"] == "CLIENT_KEYUP":
            if event_data["kb_key"] == "SHIFT":
                self.server.registry[cuuid]["char_dict"]["running"] = False
                self.notify_client(cuuid, event_data)
            elif event_data["kb_key"] == "CTRL":
                self.notify_client(cuuid, event_data)
            elif event_data["kb_key"] == "ALT":
                self.notify_client(cuuid, event_data)

        elif event_data["type"] == "CLIENT_START_BATTLE":
            self.server.registry[cuuid]["char_dict"]["running"] = False
            self.update_char_dict(cuuid, event_data["char_dict"])
            self.server.registry[cuuid]["map_name"] = event_data["map_name"]
            self.notify_client(cuuid, event_data)

        else:
            self.update_char_dict(cuuid, event_data["char_dict"])
            if "map_name" in event_data:
                self.server.registry[cuuid]["map_name"] = event_data["map_name"]
            self.notify_client(cuuid, event_data)


    def update_char_dict(self, cuuid, char_dict):
        """Updates registry with player updates.

        :param cuuid: Clients unique user identification number.
        :param char_dict: character dictionary

        :type cuuid: String
        :type event_data: String

        :rtype: None
        :returns: None

        """
        for param in char_dict:
            self.server.registry[cuuid]["char_dict"][param] = char_dict[param]


    def notify_client(self, cuuid, event_data):
        """Updates all clients with player updates.

        :param cuuid: Clients unique user identification number.
        :param event_data: Notification flag information.

        :type cuuid: String
        :type event_data: String

        :rtype: None
        :returns: None

        """
        cuuid = str(cuuid)
        event_data["type"] = "NOTIFY_" + event_data["type"]
        event_data["cuuid"] = cuuid
        for client_id in self.server.registry:
            # Don't notify a player that they themselves moved.
            if client_id == cuuid: continue

            # Notify client of the players new position.
            elif client_id != cuuid:
                self.server.notify(client_id, event_data)


    def notify_populate_client(self, cuuid, event_data):
        """Updates all clients with the details of the new client.

        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.

        :type cuuid: String
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        cuuid = str(cuuid)
        event_data["type"] = "NOTIFY_" + event_data["type"]
        event_data_1 = event_data
        for client_id in self.server.registry:
            # Don't notify a player that they themselves populated.
            if client_id == cuuid:continue

            elif client_id != cuuid:
                # Send the new client data to this client
                event_data_1["cuuid"] = cuuid
                self.server.notify(client_id, event_data_1)

                # Send this clients data to the new client
                char = self.server.registry[client_id]
                event_data_2 = {"type":event_data["type"],
                                "cuuid": client_id,
                                "event_number": event_data["event_number"],
                                "sprite_name": char["sprite_name"],
                                "map_name": char["map_name"],
                                "char_dict": char["char_dict"]
                                }
                self.server.notify(cuuid, event_data_2)


    def notify_client_interaction(self, cuuid, event_data):
        """Notify a client that another client has interacted with them.

        :param cuuid: Clients unique user identification number.
        :param event_data: Notification information.

        :type cuuid: String
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        cuuid = str(cuuid)
        event_data["type"] = "NOTIFY_" + event_data["type"]
        client_id = event_data["target"]
        event_data["target"] = cuuid
        self.server.notify(client_id, event_data)



class ControllerServer():
    """Server class for networked controller. Creates a netaria server and
    passes the network events to the local game.

    :param game: instance of the local game.

    :type game: core.control.Control object.

    :rtype: None
    :returns: None

    """

    def __init__(self, game):
        self.game = game
        self.network_events = []
        self.listening = False
        self.interfaces = {}

        # Handle users without networking support
        if not networking:
            self.server = DummyNetworking()
            return
        self.server = NeteriaServer(Controller(self))

    def update(self):
        """Updates the server state with information sent from the clients

        :param None

        :type None

        :rtype: None
        :returns: None

        """
        # Loop through our network events and pass them to the current state.
        controller_events = self.net_controller_loop()
        if controller_events:
            for controller_event in controller_events:
                self.game.key_events.append(controller_event)
                self.game.current_state.process_event(controller_event)

    def net_controller_loop(self):
        """Process all network events from controllers and pass them
        down to current State. All network events are converted to keyboard
        events for compatibility.

        :param None:

        :rtype: None
        :returns: None

        """
        events = []
        for event_data in self.network_events:
            if event_data == "KEYDOWN:up":
                event = self.game.keyboard_events["KEYDOWN"]["up"]

            elif event_data == "KEYUP:up":
                event = self.game.keyboard_events["KEYUP"]["up"]

            elif event_data == "KEYDOWN:down":
                event = self.game.keyboard_events["KEYDOWN"]["down"]

            elif event_data == "KEYUP:down":
                event = self.game.keyboard_events["KEYUP"]["down"]

            elif event_data == "KEYDOWN:left":
                event = self.game.keyboard_events["KEYDOWN"]["left"]

            elif event_data == "KEYUP:left":
                event = self.game.keyboard_events["KEYUP"]["left"]

            elif event_data == "KEYDOWN:right":
                event = self.game.keyboard_events["KEYDOWN"]["right"]

            elif event_data == "KEYUP:right":
                event = self.game.keyboard_events["KEYUP"]["right"]

            elif event_data == "KEYDOWN:enter":
                event = self.game.keyboard_events["KEYDOWN"]["enter"]

            elif event_data == "KEYUP:enter":
                event = self.game.keyboard_events["KEYUP"]["enter"]

            elif event_data == "KEYDOWN:esc":
                event = self.game.keyboard_events["KEYDOWN"]["escape"]

            elif event_data == "KEYUP:esc":
                event = self.game.keyboard_events["KEYUP"]["escape"]

            else:
                logger.debug("Unknown network event: " +str(event_data))
                event = None

            if event:
                events.append(event)

        # Clear out the network events list once all events have been processed.
        self.network_events = []
        return events



class TuxemonClient():
    """Client class for multiplayer games. Creates a netaria client and
    synchronizes the local game with the host state.

    :param game: instance of the local game.

    :type game: core.control.Control object.

    :rtype: None
    :returns: None

    """
    def __init__(self, game):

        self.game = game
        self.available_games = []
        self.server_list = []
        self.selected_game = None
        self.enable_join_multiplayer = False
        self.wait_broadcast = 0 # Used to delay autodiscover broadcast.
        self.wait_delay = 0.25  # Delay used in autodiscover broadcast.
        self.join_self = False # Default False. Set True for testing on one device.
        self.populated = False
        self.listening = False
        self.event_list = {}
        self.ping_time = 2

        # Handle users without networking support.
        if not networking:
            self.client = DummyNetworking()
            return

        self.client = NeteriaClient(server_port=40081)
        self.client.registry = {}

    def update(self, time_delta):
        """Updates the client and local game state with information sent from the server

        :param time_delta: Time since last frame.

        :type time_delta: float

        :rtype: None
        :returns: None

        """
        if self.enable_join_multiplayer:
            self.join_multiplayer(time_delta)

        if self.client.registered and not self.populated:
            self.game.isclient = True
            self.game.current_state.multiplayer_join_success_menu.text = ["Success!"]
            self.populate_player()

        if self.ping_time >= 2:
            self.ping_time = 0
            self.client_alive()
        else:
            self.ping_time += time_delta

        self.check_notify()


    def check_notify(self):
        """Checks for notify events sent from the server and updates the local client registry
        to reflect the updated information.

        :param: None

        :rtype: None
        :returns: None

        """
        for euuid, event_data in self.client.event_notifies.items():

            if event_data["type"] == "NOTIFY_CLIENT_DISCONNECTED":
                del self.client.registry[event_data["cuuid"]]
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_PUSH_SELF":
                if not event_data["cuuid"] in self.client.registry:
                    self.client.registry[str(event_data["cuuid"])]={}
                sprite = populate_client(event_data["cuuid"], event_data, self.game, self.client.registry)
                update_client(sprite, event_data["char_dict"], self.game)
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_MOVE_START":
                direction = str(event_data["direction"])
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                sprite.facing = direction
                for d in sprite.direction:
                    if sprite.direction[d]:
                        sprite.direction[d] = False
                sprite.direction[direction] = True
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_MOVE_COMPLETE":
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                sprite.final_move_dest = event_data["char_dict"]["tile_pos"]
                for d in sprite.direction:
                    if sprite.direction[d]:
                        sprite.direction[d] = False
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_MAP_UPDATE":
                self.update_client_map(event_data["cuuid"], event_data)
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_KEYDOWN":
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                if event_data["kb_key"] == "SHIFT":
                    sprite.running = True
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "CTRL":
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "ALT":
                    del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_KEYUP":
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                if event_data["kb_key"] == "SHIFT":
                    sprite.running = False
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "CTRL":
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "ALT":
                    del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_FACING":
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                if not sprite.moving:
                    sprite.facing = event_data["char_dict"]["facing"]
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_INTERACTION":
                world = self.game.get_state_name("WorldState")
                if not world:
                    return
                world.handle_interaction(event_data, self.client.registry)
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_CLIENT_START_BATTLE":
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                sprite.running = False
                sprite.final_move_dest = event_data["char_dict"]["tile_pos"]
                for d in sprite.direction:
                   if sprite.direction[d]:
                       sprite.direction[d] = False
                del self.client.event_notifies[euuid]


    def join_multiplayer(self, time_delta):
        """Joins the client to the selected server.

        :param time_delta: Time since last frame.

        :type time_delta: float

        :rtype: None
        :returns: None

        """
        # Don't allow player to join another game if they are hosting.
        if self.game.ishost:
            self.enable_join_multiplayer = False
            return False

        # If we have already joined a game end the loop.
        if self.client.registered:
            self.enable_join_multiplayer = False
            return False

        # Join a game if we have already selected one.
        if self.selected_game:
            self.client.register(self.selected_game)

        # Once per second send a server discovery packet.
        if self.wait_broadcast >= self.wait_delay:
            self.update_multiplayer_list()
            self.wait_broadcast = 0
        else:
            self.wait_broadcast += time_delta


    def update_multiplayer_list(self):
        """Sends a broadcast to 'ping' all servers on the local network. Once a server responds
        it will verify that the server is not hosted by the client who sent the ping. Once a
        server has been identified it adds it to self.available_games.

        :param None:

        :rtype: None
        :returns: None

        """
        self.client.autodiscover(autoregister=False)

        # Logic to prevent joining your own game as a client.
        if self.client.discovered_servers:

            for ip, port in self.client.discovered_servers:
                host = (ip, port)
                host_name = self.client.discovered_servers[host][1]
                try:
                    for ipa, porta in self.available_games:
                        hosta = (ipa, porta)
                        if hosta == host:
                            logger.info('Game already in list, skipping.')
                            return False
                except KeyError:
                    pass

                # Populate list of detected servers
                self.available_games.append(host)
                self.server_list.append(host_name)

    def populate_player(self, event_type="PUSH_SELF"):
        """Sends client character to the server.

        :param None
        :rtype: None
        :returns: None

        """
        if not event_type in self.event_list:
            self.event_list[event_type] = 0
        pd = prepare.player1.__dict__
        map_name = self.game.get_map_name()
        event_data = {"type": event_type,
                      "event_number": self.event_list[event_type],
                      "sprite_name": pd["sprite_name"],
                      "map_name": map_name,
                      "char_dict": {
                                  "tile_pos": pd["tile_pos"],
                                  "name": pd["name"],
                                  "facing": pd["facing"],
                                  #"monsters": pd["monsters"],
                                  #"inventory": pd["inventory"]
                                  }
                      }
        self.event_list[event_type] +=1
        self.client.event(event_data)
        self.populated = True


    def update_player(self, direction, event_type="CLIENT_MAP_UPDATE"):
        """Sends client's current map and location to the server.

        :param direction: Facing/Movement direction of clients character
        :param event_type: Event type sent to server used for event_legal() and event_execute()
        functions in middleware.

        :type direction: String
        :type type: String

        :rtype: None
        :returns: None

        """
        if not event_type in self.event_list:
            self.event_list[event_type] = 0
        pd = prepare.player1.__dict__
        map_name = self.game.get_map_name()
        event_data = {"type": event_type,
                      "event_number": self.event_list[event_type],
                      "map_name": map_name,
                      "direction": direction,
                      "char_dict": {"tile_pos": pd["tile_pos"]
                                    }
                      }
        self.event_list[event_type] +=1
        self.client.event(event_data)


    def set_key_condition(self, event):
        """Sends server information about a key condition being set or that an
        interaction has occurred.

        :param event: Pygame key event

        :type event: Dictionary

        :rtype: None
        :returns: None

        """
        if self.game.current_state != self.game.get_state_name("WorldState"):
            return False

        event_type = None
        kb_key = None
        if event.type == pg.KEYDOWN:
            event_type = "CLIENT_KEYDOWN"
            if event.key == pg.K_LSHIFT or event.key == pg.K_RSHIFT:
                kb_key = "SHIFT"
            elif  event.key == pg.K_LCTRL or event.key == pg.K_RCTRL:
                kb_key = "CTRL"
            elif event.key == pg.K_LALT or event.key == pg.K_RALT:
                kb_key = "ALT"

            elif event.key == pg.K_UP:
                kb_key = "up"
            elif event.key == pg.K_DOWN:
                kb_key = "down"
            elif event.key == pg.K_LEFT:
                kb_key = "left"
            elif event.key == pg.K_RIGHT:
                kb_key = "right"

        if event.type == pg.KEYUP:
            event_type = "CLIENT_KEYUP"
            if event.key == pg.K_LSHIFT or event.key == pg.K_RSHIFT:
                kb_key = "SHIFT"
            elif  event.key == pg.K_LCTRL or event.key == pg.K_RCTRL:
                kb_key = "CTRL"
            elif event.key == pg.K_LALT or event.key == pg.K_RALT:
                kb_key = "ALT"

            elif event.key == pg.K_UP:
                kb_key = "up"
            elif event.key == pg.K_DOWN:
                kb_key = "down"
            elif event.key == pg.K_LEFT:
                kb_key = "left"
            elif event.key == pg.K_RIGHT:
                kb_key = "right"

        if kb_key == "up" or kb_key == "down" or kb_key == "left" or kb_key == "right":
            event_type = "CLIENT_FACING"

        if not event_type in self.event_list:
            self.event_list[event_type] = 0

        if event_type and kb_key:
            if event_type == "CLIENT_FACING":
                if self.game.isclient or self.game.ishost:
                    event_data = {"type": event_type,
                                  "event_number": self.event_list[event_type],
                                  "char_dict": {"facing": kb_key}
                                  }
                    self.event_list[event_type] +=1
                    self.client.event(event_data)

            elif event_type == "CLIENT_KEYUP" or event_type == "CLIENT_KEYDOWN":
                event_data = {"type": event_type,
                              "event_number": self.event_list[event_type],
                              "kb_key": kb_key
                              }
                self.event_list[event_type] +=1
                self.client.event(event_data)


    def update_client_map(self, cuuid, event_data):
        """Updates client's current map and location to reflect the server registry.

        :param cuuid: Clients unique user identification number.
        :param event_data: Client characters current variable values.

        :type cuuid: String
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        sprite = self.client.registry[cuuid]["sprite"]
        self.client.registry[cuuid]["map_name"] = event_data["map_name"]
        update_client(sprite, event_data["char_dict"], self.game)

    def player_interact(self, sprite, interaction, event_type="CLIENT_INTERACTION", response=None):
        """Sends client to client interaction request to the server.

        :param sprite: Character sprite being interacted with.
        :param interaction: Which interaction you wish to do.

        :type sprite: core.components.player.Npc() object
        :type interaction: String

        :rtype: None
        :returns: None

        """
        if not event_type in self.event_list:
            self.event_list[event_type] = 1
        cuuid = None

        for client_id in self.client.registry:
            if self.client.registry[client_id]["sprite"] == sprite: cuuid = client_id

        pd = prepare.player1.__dict__
        event_data = {"type": event_type,
                      "event_number": self.event_list[event_type],
                      "interaction": interaction,
                      "target": cuuid,
                      "response": response,
                      "char_dict": {"monsters": pd["monsters"],
                                    "inventory": pd["inventory"]
                                    }
                      }
        self.event_list[event_type] +=1
        self.client.event(event_data)

    def route_combat(self, event):
        print(event)

    def client_alive(self):
        """Sends server a ping to let it know that it is still alive.

        :param: None
        :rtype: None
        :returns: None

        """
        event_type = "PING"
        if not event_type in self.event_list:
            self.event_list[event_type] = 1
        else:
            self.event_list[event_type] +=1

        event_data = {"type": event_type,
                      "event_number": self.event_list[event_type]}

        self.client.event(event_data)


class DummyNetworking(object):
    def __init__(self, *args, **kwargs):
        """The dummy networking object is used when networking is not supported.
        """
        self.registry = {}
        self.registered = False
        self.discovered_servers = []

    def event(self, *args, **kwargs):
        pass

    def listen(self, *args, **kwargs):
        pass

    def autodiscover(self, *args, **kwargs):
        pass


# Universal functions
def populate_client(cuuid, event_data, game, registry):
    """Creates an NPC to represent the client character and adds the
    information to the registry.

    :param cuuid: Clients unique user identification number.
    :param event_data: Event information sent by client.
    :param registry: Server or client game registry.
    :param game: Server or client Control object.

    :type cuuid: String
    :type event_data: Dictionary
    :type registry: Dictionary
    :type game: core.control.Control() object

    :rtype: core.components.player.Npc() object
    :returns: sprite

    """
    # TODO: move NPC from actions make make a common core class
    from core.components.event.actions.npc import Npc

    char_dict = event_data["char_dict"]
    sn = str(event_data["sprite_name"])
    nm = str(char_dict["name"])
    tile_pos_x = int(char_dict["tile_pos"][0])
    tile_pos_y = int(char_dict["tile_pos"][1])

    sprite = Npc().create_npc(game,(None, str(nm)+","+str(tile_pos_x)+","+str(tile_pos_y)+","+str(sn)+",network"))
    sprite.isplayer = True
    sprite.final_move_dest = sprite.tile_pos
    sprite.interactions = ["TRADE", "DUEL"]

    registry[cuuid]["sprite"] = sprite
    registry[cuuid]["map_name"] = event_data["map_name"]

    return sprite


def update_client(sprite, char_dict, game):
    """Corrects character location when it changes map or loses sync.

    :param sprite: Local NPC sprite stored in the registry.
    :param char_dict: sprite's updated variable values.
    :param game: Server or client Control object.

    :type sprite: Player or Npc object from core.components.player
    :type event_data: Dictionary
    :type game: core.control.Control() object

    :rtype: None
    :returns: None

    """
    world = game.get_state_name("WorldState")
    if not world:
        return

    for item in char_dict:
        sprite.__dict__[item] = char_dict[item]

        # Get the pixel position of our tile position.
        if item == "tile_pos":
            tile_size = prepare.TILE_SIZE
            position = [char_dict["tile_pos"][0] * tile_size[0],
                        char_dict["tile_pos"][1] * tile_size[1]
                        ]
            global_x = world.global_x
            global_y = world.global_y
            abs_position = [position[0] + global_x, position[1] + (global_y-tile_size[1])]
            sprite.__dict__["position"] = abs_position

