import pygame
from core import prepare
from core.components.menu import Menu

class ItemMenu(Menu):
    """A class to create item menu objects. The item menu allows you to view and use items in your
    inventory.

    :param screen: The pygame.display surface to draw the menu to.
    :param resolution: A tuple of the display's resolution in (x, y) format. TODO: We should be
        able to get this from pygame.display
    :param game: The main tuxemon game object that contains all the game's variables.

    :type screen: pygame.display
    :type resolution: Tuple
    :type game: core.control.Control

    To create a new menu, simply create a new menu instance and then set the size and coordinates
    of the menu like this:

    Example:

    >>> item_menu = ItemMenu(screen, resolution, self)
    >>> item_menu.size_x = 200
    >>> item_menu.size_y = 100
    >>> item_menu.pos_x = 500
    >>> item_menu.pos_y = 500
    >>> item_menu.draw()

    """

    def __init__(self, screen, resolution, game, name="Item Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, name)

        # Give this menu instance access to the main game object.
        self.game = game

        # Set the background color of our menu
        self.color = (32, 104, 96)

        # Load the item menu background image
        self.background_image = prepare.BASEDIR + "resources/gfx/ui/item/item_menu_bg.png"
        self.background_surface = pygame.image.load(self.background_image).convert()
        self.background_surface = pygame.transform.scale(self.background_surface,
            (prepare.SCREEN_SIZE[0], prepare.SCREEN_SIZE[1]))

        # Create the item menu's submenus.
        self.decision_menu = Menu(screen, resolution, game)
        self.item_list = Menu(screen, resolution, game)
        self.info_menu = Menu(screen, resolution, game)

        # Add the submenus as this menu's children
        self.add_child(self.decision_menu)
        self.add_child(self.item_list)
        self.add_child(self.info_menu)

        # Scale the sides of all the submenus
        for menu in self.children:

            # Scale the font and selection arrow to the appropriate size.
            menu.font = pygame.font.Font(
                prepare.BASEDIR + "resources/font/PressStart2P.ttf", menu.font_size * prepare.SCALE)
            menu.arrow = pygame.transform.scale(
                menu.arrow,
                (menu.arrow.get_width() * prepare.SCALE, menu.arrow.get_height() * prepare.SCALE))

            # Scale the window's borders based on the game's scale.
            for key, border in menu.border.items():
                menu.border[key] = pygame.transform.scale(
                    border,
                    (border.get_width() * prepare.SCALE, border.get_height() * prepare.SCALE))

        # Set up our submenus.
        self.decision_menu.size_x = prepare.SCREEN_SIZE[0] / 5
        self.decision_menu.size_y = prepare.SCREEN_SIZE[1] / 6
        self.decision_menu.pos_x = prepare.SCREEN_SIZE[0] - self.decision_menu.size_x - \
            (self.decision_menu.border["left-top"].get_height() * 2)
        self.decision_menu.pos_y = prepare.SCREEN_SIZE[1] - self.decision_menu.size_y - \
            (self.decision_menu.border["left-top"].get_height() * 2)
        self.decision_menu.visible = False
        self.decision_menu.interactable = False

        self.info_menu.size_x = prepare.SCREEN_SIZE[0]
        self.info_menu.size_y = int(prepare.SCREEN_SIZE[1] / 4.2)
        self.info_menu.pos_x = 0
        self.info_menu.pos_y = prepare.SCREEN_SIZE[1] - self.info_menu.size_y
        #self.info_menu.color = (0, 120, 192)
        self.info_menu.visible = True
        self.info_menu.interactable = False

        self.item_list.size_x = int((prepare.SCREEN_SIZE[0] / 3) * 2)
        self.item_list.size_y = int(prepare.SCREEN_SIZE[1] - self.info_menu.size_y)
        self.item_list.pos_x = int(prepare.SCREEN_SIZE[0] / 3)
        self.item_list.pos_y = 0
        self.item_list.visible = True
        self.item_list.interactable = True

        # Load the backpack icon
        self.backpack = {}
        self.backpack['image'] = prepare.BASEDIR + "resources/gfx/ui/item/backpack.png"
        self.backpack['surface'] = pygame.image.load(self.backpack['image']).convert_alpha()
        self.backpack['surface'] = pygame.transform.scale(
            self.backpack['surface'],
            (self.backpack['surface'].get_width() * prepare.SCALE,
             self.backpack['surface'].get_height() * prepare.SCALE))
        self.backpack['pos_x'] = (self.item_list.pos_x / 2) - \
            (self.backpack['surface'].get_width() / 2)
        self.backpack['pos_y'] = prepare.SCREEN_SIZE[1] - self.info_menu.size_y - \
            (self.backpack['surface'].get_height() * 1.2)


    def draw(self, draw_borders=True, fill_background=False):

        # We can call the draw function from our parent "Menu" class, and also draw
        # some additional stuff specifically for the Item Menu.
        Menu.draw(self, draw_borders, fill_background)

        # Draw our background image.
        self.screen.blit(self.background_surface, (0,0))

        # Draw the backpage icon.
        self.screen.blit(self.backpack['surface'],
            (self.backpack['pos_x'], self.backpack['pos_y']))

        # If the item list submenu is visible, draw it and its menu items.
        if self.item_list.visible:
            self.item_list.draw(draw_borders=False, fill_background=False)

            items = []
            for item_name, item_details in self.game.player1.inventory.items():
                items.append(item_name)

            #self.item_list.line_spacing = 250
            self.item_list.draw_textItem(items, pos_y=prepare.SCREEN_SIZE[1]/10, paging=True)

        # If the info submenu is visible, draw it and its menu items.
        if self.info_menu.visible:
            self.info_menu.draw(draw_borders=False, fill_background=True)

            # Draw the image of the currently selected item.
            if len(self.item_list.menu_items) > 0:

                # Get the selected item's description text and draw it on the info menu.
                selected_item_name = self.item_list.menu_items[self.item_list.selected_menu_item]
                info_text = self.game.player1.inventory[selected_item_name]['item'].description
                self.info_menu.draw_text(info_text, justify="center", align="middle")

                current_item_surface = self.game.player1.inventory[selected_item_name]['item'].surface

                # Scale the item's sprite if it hasn't been scaled already.
                if (prepare.SCALE != 1
                    and current_item_surface.get_size() == self.game.player1.inventory[selected_item_name]['item'].surface_size_original):
                    self.game.player1.inventory[selected_item_name]['item'].surface = pygame.transform.scale(
                        current_item_surface, (current_item_surface.get_width() * prepare.SCALE, current_item_surface.get_height() * prepare.SCALE))

                # Position the item's sprite in the middle of the left-hand part of the item list.
                item_pos_x = (self.item_list.pos_x / 2) - (current_item_surface.get_width() / 2)

                self.screen.blit(current_item_surface, (item_pos_x,0))


        # If the decision submenu is visible, draw it and its menu items.
        if self.decision_menu.visible:
            self.decision_menu.draw()
            self.decision_menu.draw_textItem(["Use", "Cancel"], 1, autoline_spacing=True)


    def get_event(self, event, game):
        # Handle when the player presses "ESC".
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:

            # If the "ESC" key was pressed while the decision menu was up, close it.
            if self.decision_menu.visible:
                self.decision_menu.visible = False
                self.decision_menu.interactable = False
                self.decision_menu.selected_menu_item = 0
                self.item_list.interactable = True

            # If no other submenus were up when we pressed "ESC", close the item menu.
            else:
                self.visible = False
                self.interactable = False

                # If the item menu was opened from combat, open up the action menu.
                if game.state_name == "COMBAT":
                    game.current_state.action_menu.visible = True
                    game.current_state.action_menu.interactable = True


        # Handle when the player presses "ENTER"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN: #and len(self.menu_items) > 0:
            # Decision Menu
            if self.decision_menu.interactable:
                if self.decision_menu.menu_items[self.decision_menu.selected_menu_item] == "Cancel":
                    self.decision_menu.visible = False
                    self.decision_menu.interactable = False
                    self.decision_menu.selected_menu_item = 0
                    self.item_list.interactable = True

                # Use the selected item.
                elif self.decision_menu.menu_items[self.decision_menu.selected_menu_item] == "Use":

                    # Get the name of the item from our menu list.
                    item_name = self.item_list.menu_items[self.item_list.selected_menu_item]

                    # For now, just use the item on the currently active monster.
                    print("Using " + item_name)
                    item_to_use = game.player1.inventory[item_name]['item']

                    # Check to see if the item can be used in the current state.
                    if game.state_name.lower() in item_to_use.usable_in:
                        print("%s can be used here!" % item_name)

                        if game.state_name == "COMBAT":
                            if item_to_use.target == "opponent":
                                item_target = game.current_state.current_players['opponent']['monster']
                            elif item_to_use.target == "player":
                                item_target = game.current_state.current_players['player']['monster']

                            # Set the player's decided action for this turn to "item" and give the name
                            # and target of the item.
                            game.current_state.current_players['player']['action'] = {'item':
                                {'name': item_name,
                                 'target': item_target}}
                        else:
                            game.player1.inventory[item_name]['item'].use(game.player1.monsters[0], game)

                    else:
                        print("%s cannot be used here!" % item_name)


            # Item List Menu
            else:
                if self.item_list.interactable:
                    print(self.item_list.menu_items[self.item_list.selected_menu_item])
                    self.decision_menu.visible = True
                    self.decision_menu.interactable = True
                    self.item_list.interactable = False

        # Handle when the player presses "Up"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:

            # Handle the decision submenu.
            if self.decision_menu.interactable:

                # If by pressing up our selected item number is less than zero, select the last
                # item in the list.
                if self.decision_menu.selected_menu_item - 1 < 0:
                    self.decision_menu.selected_menu_item = len(self.decision_menu.menu_items) - 1
                else:
                    self.decision_menu.selected_menu_item -= 1

            # If the decision menu isn't open, allow item selection.
            else:

                if self.item_list.selected_menu_item -1 < 0:
                    self.item_list.selected_menu_item = len(self.item_list.menu_items) - 1
                else:
                    self.item_list.selected_menu_item -= 1


        # Handle when the player presses "Down"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:

            # Handle the decision submenu.
            if self.decision_menu.interactable:

                # If by pressing up our selected item number is less than zero, select the last
                # item in the list.
                if self.decision_menu.selected_menu_item + 1 > len(self.decision_menu.menu_items) - 1:
                    self.decision_menu.selected_menu_item = 0
                else:
                    self.decision_menu.selected_menu_item += 1

            # If the devision menu isn't open, allow item selection.
            else:

                if self.item_list.selected_menu_item + 1 > len(self.item_list.menu_items) - 1:
                    self.item_list.selected_menu_item = 0
                else:
                    self.item_list.selected_menu_item += 1


