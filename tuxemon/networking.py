# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""This module contains the Tuxemon server and client.
"""
from __future__ import annotations

import logging
import pprint
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Literal, Tuple, TypedDict

import pygame as pg

from tuxemon import prepare
from tuxemon.middleware import Controller, Multiplayer
from tuxemon.session import local_session
from tuxemon.states import world

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

try:
    from neteria.client import NeteriaClient
    from neteria.server import NeteriaServer

    networking = True
except ImportError:
    logger.info("Neteria networking unavailable")
    networking = False

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient


class CharDict(TypedDict):
    tile_pos: Tuple[int, int]
    name: str
    facing: Literal["front", "back", "left", "right"]


class EventData(TypedDict, total=False):
    type: str
    cuuid: str
    event_number: int
    sprite_name: str
    map_name: str
    char_dict: CharDict
    kb_key: str
    target: str


class TuxemonServer:
    """Server class for multiplayer games. Creates a netaria server and
    synchronizes the local game with all client states.

    :param game: Instance of the local game.

    :type game: tuxemon.control.Control object.

    """

    def __init__(self, game: LocalPygameClient, server_name=None):

        self.game = game
        if not server_name:
            self.server_name = "Default Tuxemon Server"
        else:
            self.server_name = server_name
        self.network_events: List[str] = []
        self.listening = False
        self.interfaces = {}
        self.ips: List[str] = []

        # Handle users without networking support.
        if not networking:
            self.server = DummyNetworking()
            return

        self.server = NeteriaServer(
            Multiplayer(self),
            server_port=40081,
            server_name=self.server_name,
        )

    def update(self):
        """Updates the server state with information sent from the clients."""
        self.server_timestamp = datetime.now()
        for cuuid in self.server.registry:
            try:
                difference = (
                    self.server_timestamp
                    - self.server.registry[cuuid]["ping_timestamp"]
                )
                if difference.seconds > 15:
                    logger.info("Client Disconnected. CUUID: " + str(cuuid))
                    event_data = {"type": "CLIENT_DISCONNECTED"}
                    self.notify_client(cuuid, event_data)
                    del self.server.registry[cuuid]
                    return False

            except KeyError:
                self.server.registry[cuuid]["ping_timestamp"] = datetime.now()

    def server_event_handler(self, cuuid: str, event_data: EventData) -> None:
        """Handles events sent from the middleware that are legal.

        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.

        """
        # Only respond to the latest message of a given type
        if not "event_list" in self.server.registry[cuuid]:
            self.server.registry[cuuid]["event_list"] = {}
        elif (
            not event_data["type"] in self.server.registry[cuuid]["event_list"]
        ):
            self.server.registry[cuuid]["event_list"][event_data["type"]] = -1

        elif (
            event_data["event_number"]
            <= self.server.registry[cuuid]["event_list"][event_data["type"]]
        ):
            return
        else:
            self.server.registry[cuuid]["event_list"][
                event_data["type"]
            ] = event_data["event_number"]

        if event_data["type"] == "PUSH_SELF":
            self.server.registry[cuuid]["sprite_name"] = event_data[
                "sprite_name"
            ]
            self.server.registry[cuuid]["map_name"] = event_data["map_name"]
            self.server.registry[cuuid]["char_dict"] = event_data["char_dict"]
            self.server.registry[cuuid]["ping_timestamp"] = datetime.now()
            self.notify_populate_client(cuuid, event_data)

        elif event_data["type"] == "PING":
            self.server.registry[cuuid]["ping_timestamp"] = datetime.now()

        elif (
            event_data["type"] == "CLIENT_INTERACTION"
            or event_data["type"] == "CLIENT_RESPONSE"
        ):
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
                self.server.registry[cuuid]["map_name"] = event_data[
                    "map_name"
                ]
            self.notify_client(cuuid, event_data)

    def update_char_dict(self, cuuid: str, char_dict: CharDict) -> None:
        """Updates registry with player updates.

        :param cuuid: Clients unique user identification number.
        :param char_dict: character dictionary

        :type cuuid: String
        :type event_data: String
        """
        self.server.registry[cuuid]["char_dict"].update(char_dict)

    def notify_client(self, cuuid: str, event_data: EventData) -> None:
        """
        Updates all clients with player updates.

        Parameters:
            cuuid: Clients unique user identification number.
            event_data: Notification flag information.

        """
        cuuid = str(cuuid)
        event_data["type"] = "NOTIFY_" + event_data["type"]
        event_data["cuuid"] = cuuid
        for client_id in self.server.registry:
            # Don't notify a player that they themselves moved.
            if client_id == cuuid:
                continue

            # Notify client of the players new position.
            elif client_id != cuuid:
                self.server.notify(client_id, event_data)

    def notify_populate_client(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """Updates all clients with the details of the new client.

        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.

        :type cuuid: String
        :type event_data: Dictionary

        """
        cuuid = str(cuuid)
        event_data["type"] = "NOTIFY_" + event_data["type"]
        event_data_1 = event_data
        for client_id in self.server.registry:
            # Don't notify a player that they themselves populated.
            if client_id == cuuid:
                continue

            elif client_id != cuuid:
                # Send the new client data to this client
                event_data_1["cuuid"] = cuuid
                self.server.notify(client_id, event_data_1)

                # Send this clients data to the new client
                char = self.server.registry[client_id]
                event_data_2 = {
                    "type": event_data["type"],
                    "cuuid": client_id,
                    "event_number": event_data["event_number"],
                    "sprite_name": char["sprite_name"],
                    "map_name": char["map_name"],
                    "char_dict": char["char_dict"],
                }
                self.server.notify(cuuid, event_data_2)

    def notify_client_interaction(
        self, cuuid: str, event_data: EventData
    ) -> None:
        """Notify a client that another client has interacted with them.

        :param cuuid: Clients unique user identification number.
        :param event_data: Notification information.

        :type cuuid: String
        :type event_data: Dictionary

        """
        cuuid = str(cuuid)
        event_data["type"] = "NOTIFY_" + event_data["type"]
        client_id = event_data["target"]
        event_data["target"] = cuuid
        self.server.notify(client_id, event_data)


class ControllerServer:
    """Server class for networked controller. Creates a netaria server and
    passes the network events to the local game.

    :param game: instance of the local game.

    :type game: tuxemon.control.Control object.

    """

    def __init__(self, game: LocalPygameClient):
        self.game = game
        self.network_events: List[str] = []
        self.listening = False
        self.interfaces = {}

        # Handle users without networking support
        if not networking:
            self.server = DummyNetworking()
            return
        self.server = NeteriaServer(Controller(self))

    def update(self):
        """Updates the server state with information sent from the clients."""
        # Loop through our network events and pass them to the current state.
        controller_events = self.net_controller_loop()
        if controller_events:
            for controller_event in controller_events:
                self.game.key_events.append(controller_event)
                self.game.current_state.process_event(controller_event)

    def net_controller_loop(self):
        """
        Process all network events from controllers and pass them
        down to current State. All network events are converted to keyboard
        events for compatibility.
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
                logger.debug("Unknown network event: " + str(event_data))
                event = None

            if event:
                events.append(event)

        # Clear out the network events list once all events have been processed.
        self.network_events = []
        return events


class TuxemonClient:
    """Client class for multiplayer games. Creates a netaria client and
    synchronizes the local game with the host state.

    :param game: instance of the local game.

    :type game: tuxemon.control.Control object.

    """

    def __init__(self, game: LocalPygameClient):

        self.game = game
        # tuple = (ip, port)
        self.available_games: List[Tuple[str, int]] = []
        self.server_list: List[str] = []
        self.selected_game = None
        self.enable_join_multiplayer = False
        self.wait_broadcast = 0.0  # Used to delay autodiscover broadcast.
        self.wait_delay = 0.25  # Delay used in autodiscover broadcast.
        self.join_self = (
            False  # Default False. Set True for testing on one device.
        )
        self.populated = False
        self.listening = False
        self.event_list: Dict[str, int] = {}
        self.ping_time = 2.0

        # Handle users without networking support.
        if not networking:
            self.client = DummyNetworking()
            return

        self.client = NeteriaClient(server_port=40081)
        self.client.registry = {}

    def update(self, time_delta: float):
        """
        Updates the client and local game state with information sent from the server.

        Parameters:
            time_delta: Time since last frame.

        """
        if self.enable_join_multiplayer:
            self.join_multiplayer(time_delta)

        if self.client.registered and not self.populated:
            self.game.isclient = True
            self.populate_player()

        if self.ping_time >= 2:
            self.ping_time = 0
            self.client_alive()
        else:
            self.ping_time += time_delta

        self.check_notify()

    def check_notify(self) -> None:
        """
        Checks for notify events sent from the
        server and updates the local client registry
        to reflect the updated information.
        """
        for euuid, event_data in self.client.event_notifies.items():

            if event_data["type"] == "NOTIFY_CLIENT_DISCONNECTED":
                del self.client.registry[event_data["cuuid"]]
                del self.client.event_notifies[euuid]

            if event_data["type"] == "NOTIFY_PUSH_SELF":
                if not event_data["cuuid"] in self.client.registry:
                    self.client.registry[str(event_data["cuuid"])] = {}
                sprite = populate_client(
                    event_data["cuuid"],
                    event_data,
                    self.game,
                    self.client.registry,
                )
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
                world = self.game.get_state_by_name(world.WorldState)
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

    def join_multiplayer(self, time_delta: float):
        """
        Joins the client to the selected server.

        Parameters:
            time_delta: Time since last frame.

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
            self.wait_broadcast = 0.0
        else:
            self.wait_broadcast += time_delta

    def update_multiplayer_list(self):
        """
        Sends a broadcast to 'ping' all servers on the local network. Once a server responds
        it will verify that the server is not hosted by the client who sent the ping. Once a
        server has been identified it adds it to self.available_games.
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
                            logger.info("Game already in list, skipping.")
                            return False
                except KeyError:
                    pass

                # Populate list of detected servers
                self.available_games.append(host)
                self.server_list.append(host_name)

    def populate_player(self, event_type="PUSH_SELF"):
        """Sends client character to the server."""
        if not event_type in self.event_list:
            self.event_list[event_type] = 0
        pd = local_session.player.__dict__
        map_name = self.game.get_map_name()
        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
            "sprite_name": pd["sprite_name"],
            "map_name": map_name,
            "char_dict": {
                "tile_pos": pd["tile_pos"],
                "name": pd["name"],
                "facing": pd["facing"],
                # "monsters": pd["monsters"],
                # "inventory": pd["inventory"]
            },
        }
        self.event_list[event_type] += 1
        self.client.event(event_data)
        self.populated = True

    def update_player(
        self,
        direction: str,
        event_type: str = "CLIENT_MAP_UPDATE",
    ):
        """
        Sends client's current map and location to the server.

        Parameters:
            direction: Facing/Movement direction of clients character.
            event_type: Event type sent to server used for event_legal() and event_execute() functions in middleware.

        """
        if not event_type in self.event_list:
            self.event_list[event_type] = 0
        pd = local_session.player.__dict__
        map_name = self.game.get_map_name()
        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
            "map_name": map_name,
            "direction": direction,
            "char_dict": {"tile_pos": pd["tile_pos"]},
        }
        self.event_list[event_type] += 1
        self.client.event(event_data)

    def set_key_condition(self, event) -> None:
        """Sends server information about a key condition being set or that an
        interaction has occurred.

        :param event: Pygame key event.

        :type event: Dictionary

        """
        if self.game.current_state != self.game.get_state_by_name(
            world.WorldState
        ):
            return

        event_type = None
        kb_key = None
        if event.type == pg.KEYDOWN:
            event_type = "CLIENT_KEYDOWN"
            if event.key == pg.K_LSHIFT or event.key == pg.K_RSHIFT:
                kb_key = "SHIFT"
            elif event.key == pg.K_LCTRL or event.key == pg.K_RCTRL:
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
            elif event.key == pg.K_LCTRL or event.key == pg.K_RCTRL:
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

        if (
            kb_key == "up"
            or kb_key == "down"
            or kb_key == "left"
            or kb_key == "right"
        ):
            event_type = "CLIENT_FACING"

        if not event_type in self.event_list:
            self.event_list[event_type] = 0

        if event_type and kb_key:
            if event_type == "CLIENT_FACING":
                if self.game.isclient or self.game.ishost:
                    event_data = {
                        "type": event_type,
                        "event_number": self.event_list[event_type],
                        "char_dict": {"facing": kb_key},
                    }
                    self.event_list[event_type] += 1
                    self.client.event(event_data)

            elif (
                event_type == "CLIENT_KEYUP" or event_type == "CLIENT_KEYDOWN"
            ):
                event_data = {
                    "type": event_type,
                    "event_number": self.event_list[event_type],
                    "kb_key": kb_key,
                }
                self.event_list[event_type] += 1
                self.client.event(event_data)

    def update_client_map(self, cuuid, event_data) -> None:
        """Updates client's current map and location to reflect the server registry.

        :param cuuid: Clients unique user identification number.
        :param event_data: Client characters current variable values.

        :type cuuid: String
        :type event_data: Dictionary

        """
        sprite = self.client.registry[cuuid]["sprite"]
        self.client.registry[cuuid]["map_name"] = event_data["map_name"]
        update_client(sprite, event_data["char_dict"], self.game)

    def player_interact(
        self,
        sprite,
        interaction,
        event_type="CLIENT_INTERACTION",
        response=None,
    ):
        """Sends client to client interaction request to the server.

        :param sprite: Character sprite being interacted with.
        :param interaction: Which interaction you wish to do.

        :type sprite: tuxemon.player.Npc() object
        :type interaction: String

        :rtype: None
        :returns: None

        """
        if not event_type in self.event_list:
            self.event_list[event_type] = 1
        cuuid = None

        for client_id in self.client.registry:
            if self.client.registry[client_id]["sprite"] == sprite:
                cuuid = client_id

        pd = local_session.player.__dict__
        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
            "interaction": interaction,
            "target": cuuid,
            "response": response,
            "char_dict": {
                "monsters": pd["monsters"],
                "inventory": pd["inventory"],
            },
        }
        self.event_list[event_type] += 1
        self.client.event(event_data)

    def route_combat(self, event):
        logger.debug(event)

    def client_alive(self) -> None:
        """Sends server a ping to let it know that it is still alive.

        :param: None

        """
        event_type = "PING"
        if not event_type in self.event_list:
            self.event_list[event_type] = 1
        else:
            self.event_list[event_type] += 1

        event_data = {
            "type": event_type,
            "event_number": self.event_list[event_type],
        }

        self.client.event(event_data)


class DummyNetworking:
    def __init__(self, *args, **kwargs):
        """The dummy networking object is used when networking is not supported."""
        self.registry = {}
        self.registered = False
        # {(ip, port): (client_version_number, server_name)
        self.discovered_servers: Dict[Tuple[str, int], Tuple[int, str]] = {}
        self.event_notifies = {}

    def event(self, *args, **kwargs):
        pass

    def listen(self, *args, **kwargs):
        pass

    def autodiscover(self, *args, **kwargs):
        pass

    def register(self, *args, **kwargs):
        pass

    def notify(self, *args, **kwargs):
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
    :type game: tuxemon.control.Control() object

    :rtype: tuxemon.player.Npc() object
    :returns: sprite

    """
    # TODO: move NPC from actions make make a common core class
    # needs to use actions, or update classes
    raise NotImplementedError
    from tuxemon.event.actions import Npc

    char_dict = event_data["char_dict"]
    sn = str(event_data["sprite_name"])
    nm = str(char_dict["name"])
    tile_pos_x = int(char_dict["tile_pos"][0])
    tile_pos_y = int(char_dict["tile_pos"][1])

    sprite = Npc().create_npc(
        game,
        (
            None,
            str(nm)
            + ","
            + str(tile_pos_x)
            + ","
            + str(tile_pos_y)
            + ","
            + str(sn)
            + ",network",
        ),
    )
    sprite.isplayer = True
    sprite.final_move_dest = sprite.tile_pos
    sprite.interactions = ["TRADE", "DUEL"]

    registry[cuuid]["sprite"] = sprite
    registry[cuuid]["map_name"] = event_data["map_name"]

    return sprite


def update_client(sprite, char_dict, game) -> None:
    """Corrects character location when it changes map or loses sync.

    :param sprite: Local NPC sprite stored in the registry.
    :param char_dict: sprite's updated variable values.
    :param game: Server or client Control object.

    :type sprite: Player or Npc object from tuxemon.player
    :type event_data: Dictionary
    :type game: tuxemon.control.Control() object

    """

    # broken, b/c no global x/y
    return

    world = game.get_state_by_name(world.WorldState)

    for item in char_dict:
        sprite.__dict__[item] = char_dict[item]

        # Get the pixel position of our tile position.
        if item == "tile_pos":
            tile_size = prepare.TILE_SIZE
            position = [
                char_dict["tile_pos"][0] * tile_size[0],
                char_dict["tile_pos"][1] * tile_size[1],
            ]
            global_x = world.global_x
            global_y = world.global_y
            abs_position = [
                position[0] + global_x,
                position[1] + (global_y - tile_size[1]),
            ]
            sprite.__dict__["position"] = abs_position
