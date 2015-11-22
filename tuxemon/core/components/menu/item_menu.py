import pygame
from core import prepare
from core.components.menu import NewMenu
from core.components.ui import UserInterface

class ItemMenu(NewMenu):
    """A class to create item menu objects. The item menu allows you to view and use items in your
    inventory.

    :param screen: The pygame.display surface to draw the menu to.
    :param resolution: A tuple of the display's resolution in (x, y) format. TODO: We should be
        able to get this from pygame.display
    :param game: The main tuxemon game object that contains all the game's variables.

    :type screen: pygame.display
    :type resolution: Tuple
    :type game: core.tools.Control

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

    def __init__(self, game, size=('100%', '100%'), position=(0, 0), name="Item Menu",
                 background="resources/gfx/ui/item/item_menu_bg.png",
                 background_color=(32, 104, 96), interactable=False, visible=False,
                 children=[], parents=[], draw_border=False,
                 border_images="default", border_animation_speed=0.2,
                 arrow_images=["resources/gfx/arrow.png"], arrow_animation_speed=0.2,
                 menu_item_columns=1, menu_item_autospacing=True, menu_item_paging=False):

        # Initialize the parent menu class's default shit
        NewMenu.__init__(self, game, size=size, position=position, name=name,
                         background=background, background_color=background_color,
                         visible=visible, draw_border=draw_border)

        # Set up our menu's default position.
        resolution = prepare.SCREEN_SIZE

        # Create the item menu's submenus.
        self.decision_menu = self._create_descision_menu()
        self.info_menu = self._create_info_menu()
        self.item_list = self._create_item_list_menu()

        # Load the backpack icon
        self.backpack = UserInterface("resources/gfx/ui/item/backpack.png", (0, 0), game.screen)
        x = (self.item_list.position[0] / 2) - \
            (self.backpack.width / 2)
        y = resolution[1] - self.info_menu.size[1] - \
            (self.backpack.height * 1.2)
        self.backpack.position = [x, y]

    def _create_descision_menu(self):
        # Set up our menu's default position.
        from core import prepare, tools
        resolution = prepare.SCREEN_SIZE
        fifth_screen_width = tools.get_pos_from_percent('20%', resolution[0])
        sixth_screen_height = tools.get_pos_from_percent('16%', resolution[1])

        decision_menu = NewMenu(self.game, visible=False, interactable=False)
        width = fifth_screen_width
        height = sixth_screen_height
        x = resolution[0] - width - decision_menu.border_thickness
        y = resolution[1] - height - decision_menu.border_thickness
        decision_menu.set_size(width, height)
        decision_menu.set_position(x, y)
        decision_menu.add_text_menu_items(["Use", "Cancel"], justify="center", align="middle")

        self.add_child(decision_menu)

        return decision_menu

    def _create_info_menu(self):
        # Set up our menu's default position.
        from core import prepare, tools
        resolution = prepare.SCREEN_SIZE
        quart_screen_height = tools.get_pos_from_percent('23%', resolution[1])

        info_menu = NewMenu(self.game, visible=True, interactable=False)
        width = resolution[0]
        height = quart_screen_height
        x = 0
        y = resolution[1] - height
        info_menu.set_size(width, height)
        info_menu.set_position(x, y)
        self.add_child(info_menu)

        return info_menu

    def _create_item_list_menu(self):
        # Set up our menu's default position.
        from core import prepare, tools
        resolution = prepare.SCREEN_SIZE
        third_screen_width = tools.get_pos_from_percent('33.333%', resolution[0])
        quart_screen_height = tools.get_pos_from_percent('25%', resolution[1])

        item_list = NewMenu(self.game, visible=True, interactable=True,
                            draw_background=False, draw_border=False)
        width = third_screen_width * 2
        height = resolution[1] - self.info_menu.height
        x = third_screen_width
        y = 0
        item_list.set_size(width, height)
        item_list.set_position(x, y)
        self.add_child(item_list)

        return item_list

    def update(self, dt):
        super(NewMenu, self).update(dt)
        self.info_menu.update(dt)
        self.item_list.update(dt)
        self.decision_menu.update(dt)
        self.backpack.update(dt)

        # Update our info menu with our current selection
        selected_item = self.item_list.get_current_selection()
        if selected_item and selected_item in self.game.player1.inventory:
            info_text = self.game.player1.inventory[selected_item]['item'].description
            self.info_menu.set_text(info_text, justify="middle", align="center")
        else:
            self.info_menu.clear_text()

    def draw(self):

        # We can call the draw function from our parent "Menu" class, and also draw
        # some additional stuff specifically for the Item Menu.
        super(NewMenu, self).draw()
        if not self.visible:
            return

        self.backpack.draw()

        # If the item list submenu is visible, draw it and its menu items.
        if self.item_list.visible:
            self.item_list.draw()

            items = []
            for item_name, item_details in self.game.player1.inventory.items():
                items.append(item_name)

            #self.item_list.line_spacing = 250
            self.item_list.set_text_menu_items(items)

        # If the info submenu is visible, draw it and its menu items.
        if self.info_menu.visible:
            self.info_menu.draw()

            # Draw the image of the currently selected item.
            #if len(self.item_list.text_menu) > 0:
            #
            #    # Get the selected item's description text and draw it on the info menu.
            #    selected_item_name = self.item_list.menu_items[self.item_list.selected_menu_item]
            #    info_text = self.game.player1.inventory[selected_item_name]['item'].description
            #    self.info_menu.draw_text(info_text, justify="center", align="middle")
            #
            #    current_item_surface = self.game.player1.inventory[selected_item_name]['item'].surface
            #
            #    # Scale the item's sprite if it hasn't been scaled already.
            #    if (prepare.SCALE != 1
            #        and current_item_surface.get_size() == self.game.player1.inventory[selected_item_name]['item'].surface_size_original):
            #        self.game.player1.inventory[selected_item_name]['item'].surface = pygame.transform.scale(
            #            current_item_surface, (current_item_surface.get_width() * prepare.SCALE, current_item_surface.get_height() * prepare.SCALE))
            #
            #    # Position the item's sprite in the middle of the left-hand part of the item list.
            #    item_pos_x = (self.item_list.pos_x / 2) - (current_item_surface.get_width() / 2)
            #
            #    self.screen.blit(current_item_surface, (item_pos_x,0))


        # If the decision submenu is visible, draw it and its menu items.
        self.decision_menu.draw()


    def get_event(self, event):
        # Local access to the game
        game = self.game

        # Handle when the player presses "ESC".
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:

            # If the "ESC" key was pressed while the decision menu was up, close it.
            if self.decision_menu.visible:
                self.decision_menu.set_visible(False)
                self.decision_menu.set_interactable(False)
                self.decision_menu.selected_menu_item = 0
                self.item_list.set_interactable(True)

            # If no other submenus were up when we pressed "ESC", close the item menu.
            else:
                self.set_visible(False)
                self.set_interactable(False)

                # If the item menu was opened from combat, open up the action menu.
                if game.state_name == "COMBAT":
                    game.state.action_menu.visible = True
                    game.state.action_menu.interactable = True

        # Handle when the player presses "ENTER"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and len(self.item_list.text_menu) > 0:
            # Decision Menu
            if self.decision_menu.interactable:
                if self.decision_menu.get_current_selection() == "Cancel":
                    self.decision_menu.set_visible(False)
                    self.decision_menu.set_interactable(False)
                    self.decision_menu.selected_menu_item = 0
                    self.item_list.set_interactable(True)

                # Use the selected item.
                elif self.decision_menu.get_current_selection() == "Use":

                    # Get the name of the item from our menu list.
                    item_name = self.item_list.get_current_selection()

                    # For now, just use the item on the currently active monster.
                    print "Using " + item_name
                    item_to_use = game.player1.inventory[item_name]['item']

                    # Check to see if the item can be used in the current state.
                    if game.state_name.lower() in item_to_use.usable_in:
                        print "%s can be used here!" % item_name

                        if game.state_name == "COMBAT":
                            if item_to_use.target == "opponent":
                                item_target = game.state.current_players['opponent']['monster']
                            elif item_to_use.target == "player":
                                item_target = game.state.current_players['player']['monster']

                            # Set the player's decided action for this turn to "item" and give the name
                            # and target of the item.
                            game.state.current_players['player']['action'] = {'item':
                                {'name': item_name,
                                 'target': item_target}}
                        else:
                            game.player1.inventory[item_name]['item'].use(game.player1.monsters[0], game)
                        self.decision_menu.set_interactable(False)
                        self.decision_menu.set_visible(False)
                        self.item_list.set_interactable(True)

                    else:
                        print "%s cannot be used here!" % item_name

            # Item List Menu
            else:
                if self.item_list.interactable:
                    self.item_list.get_current_selection()
                    self.decision_menu.set_visible(True)
                    self.decision_menu.set_interactable(True)
                    self.item_list.set_interactable(False)

        # Handle when the player presses "Up"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:

            # Handle the decision submenu.
            if self.decision_menu.interactable:
                self.decision_menu.menu_select_prev()

            # If the decision menu isn't open, allow item selection.
            else:
                self.item_list.menu_select_prev()

        # Handle when the player presses "Down"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:

            # Handle the decision submenu.
            if self.decision_menu.interactable:
                self.decision_menu.menu_select_next()

            # If the decision menu isn't open, allow item selection.
            else:
                self.item_list.menu_select_next()
