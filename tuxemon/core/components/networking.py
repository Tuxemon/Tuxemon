from middleware import Multiplayer
from core.components import player
from core.components.event.actions.npc import Npc
from core import prepare

from neteria.server import NeteriaServer
from neteria.client import NeteriaClient

import netifaces
import pprint
import pygame

# Create a logger for optional handling of debug messages.
import logging
logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

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
        self.interfaces = {}
        self.ips = []
        
        for device in netifaces.interfaces():
            interface = netifaces.ifaddresses(device)
            try:
                self.interfaces[device] = interface[netifaces.AF_INET][0]['addr']
            except KeyError:
                pass
        
        for interface in self.interfaces:
                        ip = self.interfaces[interface]
                        if ip == "127.0.0.1": continue
                        else: self.ips.append(ip)
        

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
    
    
    def server_event_handler(self, cuuid, event_data):
        """Handles events sent from the middleware that are legal.

        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.
        
        :type cuuid: String 
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        if event_data["type"] == "PUSH_SELF":
            sprite = populate_client(cuuid, event_data, self.server.registry, self.game)
            update_client_location(sprite, event_data["char_dict"], self.game)
            self.notify_populate_client(cuuid, event_data, sprite)
            
        elif event_data["type"] =="CLIENT_MOVE_START":
            #pp.pprint("Client Move Start")
            #pp.pprint(event_data)
            direction = str(event_data["direction"])
            sprite = self.server.registry[cuuid]["sprite"]
            char_dict = event_data["char_dict"]
            sprite.facing = direction
            for d in sprite.direction:
                if sprite.direction[d]: sprite.direction[d] = False
            sprite.direction[direction] = True
            self.notify_client_move(cuuid,
                                    sprite,
                                    char_dict["tile_pos"],
                                    event_data["direction"]
                                    )
       
        elif event_data["type"] == "CLIENT_MOVE_COMPLETE":
            #pp.pprint("Client Move Complete")
            #pp.pprint(event_data)
            sprite = self.server.registry[cuuid]["sprite"]
            char_dict = event_data["char_dict"]
            self.notify_client_move(cuuid,
                                    sprite,
                                    char_dict["tile_pos"],
                                    sprite.facing,
                                    event_type="NOTIFY_MOVE_COMPLETE"
                                    )
            for d in sprite.direction:
                if sprite.direction[d]: sprite.direction[d] = False
            sprite.final_move_dest = char_dict["tile_pos"]
            
        elif event_data["type"] =="CLIENT_MAP_UPDATE":
            self.update_client_map(cuuid, event_data)
            
        elif event_data["type"] == "CLIENT_KEYDOWN":
            sprite = self.server.registry[cuuid]["sprite"]
            if event_data["kb_key"] == "SHIFT":
                sprite.running = True
                self.notify_key_condition(cuuid, event_data["kb_key"], event_data["type"])
            elif event_data["kb_key"] == "CRTL":
                pass
            elif event_data["kb_key"] == "ALT":
                pass
        
        elif event_data["type"] == "CLIENT_KEYUP":
            sprite = self.server.registry[cuuid]["sprite"]
            if event_data["kb_key"] == "SHIFT":
                sprite.running = False
                self.notify_key_condition(cuuid, event_data["kb_key"], event_data["type"])
            elif event_data["kb_key"] == "CRTL":
                pass
            elif event_data["kb_key"] == "ALT":
                pass
        
        
    def update_client_map(self, cuuid, event_data=None):
        """Updates client's current map and location in the server registry.

        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.
        
        :type cuuid: String 
        :type event_data: Dictionary

        :rtype: None
        :returns: None

        """
        sprite = None
        if event_data:
            self.server.registry[cuuid]["map_name"] = event_data["map_name"]
            sprite = self.server.registry[cuuid]["sprite"]
            update_client_location(sprite, event_data["char_dict"], self.game)
            map_name = event_data["map_name"]
            char_dict = event_data["char_dict"]
        
        if not event_data:
            map_name = self.game.get_map_name()
            char_dict = {"tile_pos": self.game.state_dict["WORLD"].player1.tile_pos}
            
        
        for client_id in self.server.registry:
            # Don't notify a player that they themselves moved.
            if sprite:
                if sprite == self.server.registry[client_id]["sprite"]: continue
            
            # Notify client of the players new position.
            event_data = {"type": "NOTIFY_CLIENT_MAP",
                          "cuuid": cuuid,
                          "map_name": map_name,
                          "char_dict": char_dict
                          }
            self.server.notify(client_id, event_data)


    def notify_client_move(self, cuuid, sprite, tile_pos, facing, event_type="NOTIFY_CLIENT_MOVE"):
        """Updates all clients with location a player that moved.
        
        :param cuuid: Clients unique user identification number.
        :param sprite: Clients local copy of their character.
        :param tile_pos: Client characters current global location.
        :param facing: Direction character is facing.
        :param event_type: Notification flag information.
        
        :type cuuid: String
        :type sprite: Player or Npc object from core.components.player
        :type tile_pos: Tuple
        :type facing: String
        :type event_type: String
        
        :rtype: None
        :returns: None

        """
        cuuid = str(cuuid)

        for client_id in self.server.registry:
            # Don't notify a player that they themselves moved.
            if client_id == cuuid: continue
        
            # Notify client of the players new position.
            elif client_id != cuuid:
                event_data = {"type": event_type,
                              "cuuid": cuuid,
                              "direction": facing,
                              "char_dict":{"tile_pos": tile_pos
                                           }
                              }
                #pp.pprint(event_type)
                #pp.pprint(event_data)
                self.server.notify(client_id, event_data)


    def notify_populate_client(self, cuuid, event_data, sprite):
        """Updates all clients with location a player that moved.
        
        :param cuuid: Clients unique user identification number.
        :param event_data: Event information sent by client.
        :param sprite: Clients local copy of their character.
        
        :type cuuid: String
        :type event_data: Dictionary
        :type sprite: Player or Npc object from core.components.player
        
        :rtype: None
        :returns: None

        """
        for client_id in self.server.registry:
            # Don't notify a player that they themselves populated.
            if client_id == cuuid:continue
            
            elif client_id != cuuid:
                # Send the new client data to this client
                new_event_data_1 = {"type": "NOTIFY_CLIENT_NEW",
                                  "cuuid": cuuid,
                                  "sprite_name": event_data["sprite_name"],
                                  "map_name": event_data["map_name"],
                                  "char_dict": event_data["char_dict"]
                                  }
                #pp.pprint("new_event_data_1")
                #pp.pprint(new_event_data_1)
                self.server.notify(client_id, new_event_data_1)
                
                # Send this clients data to the new client
                pd = self.server.registry[client_id]["sprite"].__dict__
                new_event_data_2 = {"type": "NOTIFY_CLIENT_NEW",
                                  "cuuid": client_id,
                                  "sprite_name": pd["sprite_name"],
                                  "map_name": self.server.registry[client_id]["map_name"],
                                  "char_dict": {"tile_pos": pd["tile_pos"],
                                                "name": pd["name"],
                                                "facing": pd["facing"]
                                                } 
                                  }
                #pp.pprint("new_event_data_2")
                #pp.pprint(new_event_data_2)
                self.server.notify(cuuid, new_event_data_2)
                
        
        # Send server characters data to the new client
        # Server's character is not in the registry
        map_name = self.game.get_map_name()
        pd2 = self.game.state_dict["WORLD"].player1.__dict__
        new_event_data_3 = {"type": "NOTIFY_CLIENT_NEW",
                          "cuuid": str(self.game.client.client.cuuid),
                          "sprite_name": event_data["sprite_name"],
                          "map_name": map_name,
                          "char_dict": {"tile_pos": pd2["tile_pos"],
                                        "name": pd2["name"],
                                        "facing": pd2["facing"]
                                        } 
                          }
        #pp.pprint("new_event_data_3")
        #pp.pprint(new_event_data_3)
        self.server.notify(cuuid, new_event_data_3)
    
    def notify_key_condition(self, cuuid, kb_key, event_type):
        """Updates all clients with location a player that moved.
        
        :param cuuid: Clients unique user identification number.
        :param kb_key: Key being pressed that modifies client behavior.
        :param event_type: Notification flag information.
        
        :type cuuid: String
        :type kb_key: String
        :type event_type: String
        
        :rtype: None
        :returns: None

        """
        cuuid = str(cuuid)
        event_type = "NOTIFY_" + event_type
        for client_id in self.server.registry:
            # Don't notify a player that they themselves moved.
            if client_id == cuuid: continue
        
            # Notify client of the players new position.
            elif client_id != cuuid:
                event_data = {"type": event_type,
                              "cuuid": cuuid,
                              "kb_key": kb_key,
                              }
                pp.pprint(event_type)
                pp.pprint(event_data)
                self.server.notify(client_id, event_data)


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
        self.client.registry = {}
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
            self.game.state_dict["PC"].multiplayer_join_success_menu.text = ["Success!"]
            self.populate_player()
        
        self.check_notify()

    
    def check_notify(self):
        """Checks for notify events sent from the server and updates the local client registry
        to reflect the updated information.

        :param: None
        
        :rtype: None
        :returns: None

        """ 
        for euuid, event_data in self.client.event_notifies.items():
            
            if event_data["type"] == "NOTIFY_CLIENT_NEW":
                #pp.pprint("Notify Client New")
                #pp.pprint(event_data)
                if not event_data["cuuid"] in self.client.registry:
                    self.client.registry[str(event_data["cuuid"])]={}
                sprite = populate_client(event_data["cuuid"], event_data, self.client.registry, self.game)
                update_client_location(sprite, event_data["char_dict"], self.game)
                del self.client.event_notifies[euuid]
                
            if event_data["type"] == "NOTIFY_CLIENT_MOVE":
                direction = str(event_data["direction"])
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                sprite.facing = direction
                sprite.direction[direction] = True
                del self.client.event_notifies[euuid]
            
            if event_data["type"] == "NOTIFY_MOVE_COMPLETE":
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                sprite.final_move_dest = event_data["char_dict"]["tile_pos"]
                for d in sprite.direction:
                    if sprite.direction[d]: sprite.direction[d] = False
                del self.client.event_notifies[euuid]
            
            if event_data["type"] == "NOTIFY_CLIENT_MAP":
                self.update_client_map(event_data["cuuid"], event_data)
                del self.client.event_notifies[euuid]
            
            if event_data["type"] == "NOTIFY_CLIENT_KEYDOWN":
                print "!"
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                if event_data["kb_key"] == "SHIFT":
                    sprite.running = True
                    print sprite.running
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "CRTL":
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "ALT":
                    del self.client.event_notifies[euuid]
                
        
            if event_data["type"] == "NOTIFY_CLIENT_KEYUP":
                print "!!"
                sprite = self.client.registry[event_data["cuuid"]]["sprite"]
                if event_data["kb_key"] == "SHIFT":
                    sprite.running = False
                    print sprite.running
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "CRTL":
                    del self.client.event_notifies[euuid]
                elif event_data["kb_key"] == "ALT":
                    del self.client.event_notifies[euuid]
            
                

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
        it will verify that the server is not hosted by the client who sent the ping. Once a 
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
        map_name = self.game.get_map_name()
        event_data = {"type": "PUSH_SELF",
                      "sprite_name": pd["sprite_name"],
                      "map_name": map_name,
                      "char_dict": {
                                  "tile_pos": pd["tile_pos"],
                                  "name": pd["name"],
                                  "facing": pd["facing"]
                                  }
                      }
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
        pd = self.game.state_dict["WORLD"].player1.__dict__
        map_name = self.game.get_map_name()
        event_data = {"type": event_type,
                      "map_name": map_name,
                      "direction": direction,
                      "char_dict": {"tile_pos": pd["tile_pos"]
                                    }
                      }
        #pp.pprint("Update player")
        #pp.pprint(event_data)
        self.client.event(event_data)
    
    
    def set_key_condition(self, event):
        """Sends server information about a key condition being set or that an
        interaction has occurred.

        :param event: Pygame key event
        
        :type event: Dictionary

        :rtype: None
        :returns: None

        """
        event_type = None
        kb_key = None
        if event.type == pygame.KEYDOWN:
            event_type = "CLIENT_KEYDOWN"
            if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                kb_key = "SHIFT"
            elif  event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                kb_key = "CTRL"
            elif event.key == pygame.K_LALT or event.key == pygame.K_RALT:
                kb_key = "ALT"
                
        if event.type == pygame.KEYUP:
            event_type = "CLIENT_KEYUP"
            if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                kb_key = "SHIFT"
            elif  event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                kb_key = "CTRL"
            elif event.key == pygame.K_LALT or event.key == pygame.K_RALT:
                kb_key = "ALT"
        
        if event_type and kb_key:
            if self.client.registered and self.game.client.populated:
                event_data = {"type": event_type,
                              "kb_key": kb_key
                              }
                self.client.event(event_data)
        
            # If we are the server send our condition info to the clients.
            if self.game.server.server.registry:
                event_type = "NOTIFY_" + event_type
                print event_type
                self.game.server.notify_key_condition(str(self.client.cuuid), kb_key, event_type)
        
            
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
        update_client_location(sprite, event_data["char_dict"], self.game)
    

# Universal functions
def populate_client(cuuid, event_data, registry, game):
    """Creates an NPC to represent the client character and adds the
    information to the registry. 
    
    :param cuuid: Clients unique user identification number.
    :param event_data: Event information sent by client.
    :param registry: Server or client game registry.
    :param game: Server or client Control object.
    
    :type cuuid: String 
    :type event_data: Dictionary
    :type registry: Dictionary
    :type game: core.tools.Control() object

    :rtype: core.components.player.Npc() object
    :returns: sprite

    """
    char_dict = event_data["char_dict"]
    sn = str(event_data["sprite_name"])
    nm = str(char_dict["name"])
    tile_pos_x = int(char_dict["tile_pos"][0])
    tile_pos_y = int(char_dict["tile_pos"][1])
    
    sprite = Npc().create_npc(game,(None, str(nm)+","+str(tile_pos_x)+","+str(tile_pos_y)+","+str(sn)+",network"))
    sprite.isplayer = True
    sprite.final_move_dest = sprite.tile_pos
    
    registry[cuuid]["sprite"] = sprite
    registry[cuuid]["map_name"] = event_data["map_name"]
    client = registry[cuuid]["sprite"]
    
    return sprite


def update_client_location(sprite, char_dict, game):
    """Corrects character location when it changes map or loses sync.

    :param sprite: Local NPC sprite stored in the registry.
    :param char_dict: sprite's updated variable values.
    :param game: Server or client Control object.
    
    :type sprite: Player or Npc object from core.components.player
    :type event_data: Dictionary
    :type game: core.tools.Control() object

    :rtype: None
    :returns: None

    """
    for item in char_dict:
        
        sprite.__dict__[item] = char_dict[item]
        
        # Get the pixel position of our tile position.
        if item == "tile_pos":
            tile_size = game.state_dict["WORLD"].tile_size
            position = [char_dict["tile_pos"][0] * tile_size[0],
                        char_dict["tile_pos"][1] * tile_size[1]
                        ]
            global_x = game.state_dict["WORLD"].global_x
            global_y = game.state_dict["WORLD"].global_y
            abs_position = [position[0] + global_x, position[1] + (global_y-tile_size[1])]
            sprite.__dict__["position"] = abs_position

