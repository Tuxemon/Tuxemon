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
# core.components.menu.pc_menu
#
"""This module contains the PC Menu
"""
from core.components.menu import Menu
from core import prepare
# Import the android mixer if on the android platform



class PCMenu(Menu):
    
    def __init__(self, screen, resolution, game, name="PC Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay
        
           
    def menu_event(self, event=None):
        """Run once a menu item has been selected by  the core.tools.Control 
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        if self.menu_items[self.selected_menu_item] == "MULTIPLAYER":
            self.game.state.multiplayer_menu.previous_menu = self
            self.game.state.multiplayer_menu.visible = True
            self.game.state.multiplayer_menu.interactable = True
            self.game.state.pc_menu.interactable = False
        elif self.menu_items[self.selected_menu_item] == "LOG OFF":
            self.game.state.next = self.game.state.previous
            self.game.flip_state()
        
        

class Multiplayer_Menu(Menu):
    
    def __init__(self, screen, resolution, game, name="MULTIPLAYER"):
        
        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay
    
    
    def menu_event(self, event=None):
        """Run once a menu item has been selected by  the core.tools.Control 
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        
        if self.menu_items[self.selected_menu_item] == "JOIN":
            if not self.game.ishost:
                self.game.state.multiplayer_join_menu.previous_menu = self
                self.game.state.multiplayer_join_menu.visible = True
                self.game.state.multiplayer_join_menu.interactable = True
                self.game.state.multiplayer_menu.interactable = False
                self.game.client.enable_join_multiplayer = True
                self.game.client.listening = True
                self.game.client.client.listen()
            else:
                return False    
                   
        elif self.menu_items[self.selected_menu_item] == "HOST":
            if not self.game.isclient:
                self.game.state.multiplayer_host_menu.previous_menu = self
                self.game.state.multiplayer_host_menu.visible = True
                self.game.state.multiplayer_host_menu.interactable = True
                self.game.state.multiplayer_menu.interactable = False
                self.game.server.listening = True
                self.game.ishost = True
                self.game.server.server.listen()
                
                # Enable the client and auto join our own game.
                self.game.client.enable_join_multiplayer = True
                self.game.client.listening = True
                self.game.client.client.listen()
                
                while not self.game.client.client.registered:
                    self.game.client.client.autodiscover(autoregister=False)
    
                    if self.game.client.client.discovered_servers > 0:
                        for ip, port in self.game.client.client.discovered_servers:
                                for interface in self.game.client.interfaces:
                                    if ip == self.game.client.interfaces[interface]:
                                        game = (ip, 40081)
                                        self.game.client.client.register(game)
            
            else:
                return False


class Multiplayer_Join_Menu(Menu):
    
    def __init__(self, screen, resolution, game, name="JOIN"):
        
        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay
        
    
    def menu_event(self, event=None):
        """Run once a menu item has been selected by  the core.tools.Control 
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        try:
            self.game.client.selected_game = (self.menu_items[self.selected_menu_item], 
                                       self.game.client.available_games[self.menu_items[self.selected_menu_item]])
        except IndexError:
            pass
        
        if self.game.client.selected_game:
            self.game.state.multiplayer_join_success_menu.previous_menu = self
            self.game.state.multiplayer_join_success_menu.visible = True
            self.game.state.multiplayer_join_success_menu.interactable = True
            self.game.state.multiplayer_join_menu.interactable = False


class Multiplayer_Join_Success_Menu(Menu):
    
    def __init__(self, screen, resolution, game, name="SUCCESS"):
        
        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay
        self.text = ["Joining. Please wait..."]
        
    
    def menu_event(self, event=None):
        """Run once a menu item has been selected by  the core.tools.Control 
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        return False
            
            
class Multiplayer_Host_Menu(Menu):
    
    def __init__(self, screen, resolution, game, name="HOSTING"):
        
        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, game, name)
        self.delay = 0.5
        self.elapsed_time = self.delay
        self.text = ["Server started:"]
        for ip in self.game.server.ips:
            self.text.append(ip)
    
    def menu_event(self, event=None):
        """Run once a menu item has been selected by  the core.tools.Control 
        get_menu_event() function

        :param None:

        :rtype: None
        :returns: None

        """
        return False
            
            
        