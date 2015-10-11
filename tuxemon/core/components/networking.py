from middleware import Multiplayer
from core.components import player
from core import prepare

from neteria.server import NeteriaServer
from neteria.client import NeteriaClient

import netifaces
import pygame

# Create a logger for optional handling of debug messages.
import logging
logger = logging.getLogger(__name__)

class TuxemonServer():
    """Server class for multiplayer games. Creates a netaria server and
    synchronizes the local game with all client states.

    :param game: instance of the local game.
    
    :type game: core.tools.Control object.

    :rtype: None
    :returns: None

    """
    
    def __init__(self, game):
        self.game = game
        self.server = NeteriaServer(Multiplayer(self.game, self))
        self.network_events = []
        self.listening = False
        
        
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
                self.game.state.get_event(controller_event)


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
                self.keys[pg.K_UP] = 1
                event = self.game.keyboard_events["KEYDOWN"]["up"]

            elif event_data == "KEYUP:up":
                self.keys[pg.K_UP] = 0
                event = self.game.keyboard_events["KEYUP"]["up"]

            elif event_data == "KEYDOWN:down":
                self.keys[pg.K_DOWN] = 1
                event = self.game.keyboard_events["KEYDOWN"]["down"]

            elif event_data == "KEYUP:down":
                self.keys[pg.K_DOWN] = 0
                event = self.game.keyboard_events["KEYUP"]["down"]

            elif event_data == "KEYDOWN:left":
                self.keys[pg.K_LEFT] = 1
                event = self.game.keyboard_events["KEYDOWN"]["left"]

            elif event_data == "KEYUP:left":
                self.keys[pg.K_LEFT] = 0
                event = self.game.keyboard_events["KEYUP"]["left"]

            elif event_data == "KEYDOWN:right":
                self.keys[pg.K_RIGHT] = 1
                event = self.game.keyboard_events["KEYDOWN"]["right"]

            elif event_data == "KEYUP:right":
                self.keys[pg.K_RIGHT] = 0
                event = self.game.keyboard_events["KEYUP"]["right"]

            elif event_data == "KEYDOWN:enter":
                self.keys[pg.K_RETURN] = 1
                event = self.game.keyboard_events["KEYDOWN"]["enter"]

            elif event_data == "KEYUP:enter":
                self.keys[pg.K_RETURN] = 0
                event = self.game.keyboard_events["KEYUP"]["enter"]

            elif event_data == "KEYDOWN:esc":
                self.keys[pg.K_ESCAPE] = 1
                event = self.game.keyboard_events["KEYDOWN"]["escape"]

            elif event_data == "KEYUP:esc":
                self.keys[pg.K_ESCAPE] = 0
                event = self.game.keyboard_events["KEYUP"]["escape"]
            
            else:
                logger.debug("Unknown network event: " +str(event_data))
                event = None

            if event:
                events.append(event)
        
        # Clear out the network events list once all events have been processed.
        self.network_events = []
        return events
    
    
    def populate_client(self, cuuid, event_data):
        """Creates a local NPC to represent the client character and adds the
        iformation to the server registry. 
        
        :param cuuid: Clients unique user identification number.
        :param event_data: Client characters current variable values.
        
        :type cuuid: String 
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        self.server.registry[cuuid]["map_name"] = event_data["map_name"]
        char_dict = event_data["char_dict"]
        sn = str(event_data["sprite_name"])
        nm = str(char_dict["name"])
        sprite = player.Npc(sprite_name=sn, 
                             name=nm)
        self.server.registry[cuuid]["sprite"] = sprite
        client = self.server.registry[cuuid]["sprite"]
        self.game.scale_new_player(client)
        self.update_client(client, char_dict)


    def update_client(self, client, char_dict):
        """Adds updated client character information to the local server registry.

        :param client: Clients local NPC sprite stored in the server registry.
        :param char_dict: Client characters current variable values.
        
        :type client: core.components.player.Npc() module 
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        for item in char_dict:
            if item != "tile_pos":
                client.__dict__[item] = char_dict[item]
            elif item == "tile_pos":
                tile_size = self.game.state_dict["WORLD"].tile_size
                abs_position = [char_dict["tile_pos"][0] * tile_size[0],
                                char_dict["tile_pos"][1] * tile_size[1]]
                global_x = self.game.state_dict["WORLD"].global_x
                global_y = self.game.state_dict["WORLD"].global_y
                position = [abs_position[0] + global_x, abs_position[1] + (global_y-tile_size[1])]
                client.__dict__["position"] = position


    def move_client_npc(self, cuuid, event_data):
        """Moves the client character in the local game.

        :param cuuid: Clients unique user identification number.
        :param event_data: Client characters current status.
        
        :type cuuid: String 
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        client = self.server.registry[cuuid]["sprite"]
        char_dict = event_data["char_dict"]
        
        self.server.registry[cuuid]["map_name"] = event_data["map_name"]
        self.update_client(client, char_dict)
        client.facing = event_data["direction"]
#         if event_data["key"] == "KEYDOWN":
#             client.direction[event_data["direction"]] = True
#                 
#         elif event_data["key"] == "KEYUP":
#             client.direction[event_data["direction"]] = False


class TuxemonClient():
    """Client class for multiplayer games. Creates a netaria client and
    synchronizes the local game with the host state.

    :param game: instance of the local game.
    
    :type game: core.tools.Control object.

    :rtype: None
    :returns: None

    """
    
    def __init__(self, game):
        self.game = game
        self.client = NeteriaClient()
        self.interfaces = {}
        
        for device in netifaces.interfaces():
            interface = netifaces.ifaddresses(device)
            try:
                self.interfaces[device] = interface[netifaces.AF_INET][0]['addr']
            except KeyError:
                pass
        
        self.available_games = {}
        self.server_list = []
        self.selected_game = None
        self.enable_join_multiplayer = False
        self.wait_broadcast = 0 # Used to delay autodiscover broadcast.
        self.join_self = True # Default False. Set True for testing on one device.
        self.populated = False
        self.listening = False
    
    
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
            self.populate_player()
            
            
    
    def join_multiplayer(self, time_delta):
        """Joins the client to the selected server.

        :param time_delta: Time since last frame.
        
        :type time_delta: float 

        :rtype: None
        :returns: None

        """ 
        # If we have already joined a game end the loop 
        if self.client.registered:
            self.enable_join_multiplayer = False
            return False
        
        # Join a game if we have already selected one.
        if self.selected_game:
            self.client.register(self.selected_game)
        
        # Once per second send a server discovery packet. 
        if self.wait_broadcast >= 1:
            self.update_multiplayer_list()
            self.wait_broadcast = 0
        else: self.wait_broadcast += time_delta
        
        
    def update_multiplayer_list(self):
        """Sends a broadcast to 'ping' all servers on the local network. Once a server responds
        it  will verify that the server is not hosted by the client who sent the ping. Once a 
        server has been identified it adds it to self.available_games.

        :param None:

        :rtype: None
        :returns: None

        """
            
        self.client.autodiscover(autoregister=False)
    
        # Logic to prevent joining your own game as a client.
        if self.client.discovered_servers > 0:
            for ip, port in self.client.discovered_servers:
                try: 
                    if self.available_games[ip]:
                        logger.info('Game already in list, skipping.')
                        return False
                except KeyError:
                    pass
                if not self.join_self:
                    for interface in self.interfaces:
                        if ip == self.interfaces[interface]:
                            logger.info('Users server responded to users own broadcast, Deleting entry.')
                            del self.client.discovered_servers[(ip, port)]
                            return False
#                         
                # Populate list of detected servers   
                self.available_games[ip] = port
            
        for item in self.available_games.items():
            self.server_list.append(item[0])
        
    
    def populate_player(self):
        """Sends client character to the server.

        :param None
        :rtype: None
        :returns: None

        """
        pd = self.game.state_dict["WORLD"].player1.__dict__
        map_path = self.game.state_dict["WORLD"].current_map.filename
        map_name = str(map_path.replace(prepare.BASEDIR, ""))
        
        event_data = {"type": "PUSH_SELF",
                      "map_name": map_name,
                      "sprite_name": "player1",
                      "char_dict": {
                                  "tile_pos": pd["tile_pos"],
                                  "game_variables": pd["game_variables"],
                                  "inventory": pd["inventory"],
                                  "tile_size": pd["tile_size"],
                                  "runrate": pd["runrate"],
                                  "monsters": pd["monsters"],
                                  "direction": pd["direction"],
                                  "running": pd["running"],
                                  "moving": pd["moving"],
                                  "walkrate": pd["walkrate"],
                                  "name": pd["name"],
                                  "party_limit": pd["party_limit"],
                                  "moverate": pd["moverate"],
                                  "facing": pd["facing"],
                                  }
                      }
        self.client.event(event_data)
        self.populated = True
    
    
    def move_player(self, event=None):
        """Sends client character movement events to the server.

        :param event: Input event passed from core.tools.Control event_loop.
        
        :type event: Pygame Event.
        
        :rtype: None
        :returns: None

        """
        key = None
        direction = None
        pd = self.game.state_dict["WORLD"].player1.__dict__
        map_path = self.game.state_dict["WORLD"].current_map.filename
        map_name = str(map_path.replace(prepare.BASEDIR, ""))
        
        # Don't move if we are in a menu
        if not self.game.state.menu_blocking:
            
            if event:
                # Handle Key DOWN events
                if event.type == pygame.KEYDOWN:
                   
                    if event.key == pygame.K_UP:
                        key = "KEYDOWN"
                        direction = "up"
                    if event.key == pygame.K_DOWN:
                        key = "KEYDOWN"
                        direction = "down"
                    if event.key == pygame.K_LEFT:
                        key = "KEYDOWN"
                        direction = "left"
                    if event.key == pygame.K_RIGHT:
                        key = "KEYDOWN"
                        direction = "right"
    
                # Handle Key UP events
                if event.type == pygame.KEYUP:
                        
                    if event.key == pygame.K_UP:
                        key = "KEYUP"
                        direction = "up"
                    if event.key == pygame.K_DOWN:
                        key = "KEYUP"
                        direction = "down"
                    if event.key == pygame.K_LEFT:
                        key = "KEYUP"
                        direction = "left"
                    if event.key == pygame.K_RIGHT:
                        key = "KEYUP"
                        direction = "right"
                
                if direction and key:
                    
                    event_data = {"type": "CLIENT_EVENT",
                                  "direction": direction,
                                  "key": key,
                                  "map_name": map_name,
                                  "char_dict": {"tile_pos": pd["tile_pos"],
                                                "runrate": pd["runrate"],
                                                "running": pd["running"],
                                                "moving": pd["moving"],
                                                "walkrate": pd["walkrate"],
                                                "moverate": pd["moverate"],
                                                }
                                  }
                    self.client.event(event_data)
            
    
    
        
        
        
    