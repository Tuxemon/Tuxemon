
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
            self.game.state.multiplayer_join_menu.previous_menu = self
            self.game.state.multiplayer_join_menu.visible = True
            self.game.state.multiplayer_join_menu.interactable = True
            self.game.state.multiplayer_menu.interactable = False
            self.game.client.enable_join_multiplayer = True
            self.game.client.listening = True 
            self.game.client.client.listen()    
                   
        elif self.menu_items[self.selected_menu_item] == "HOST":
            self.game.state.multiplayer_host_menu.previous_menu = self
            self.game.state.multiplayer_host_menu.visible = True
            self.game.state.multiplayer_host_menu.interactable = True
            self.game.state.multiplayer_menu.interactable = False
            self.game.server.listening = True
            self.game.server.server.listen()



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
        pass
            
            
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
        pass
            
            
        