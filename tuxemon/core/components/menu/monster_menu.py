import pygame
from core import prepare
from core.components.menu import Menu
from core.components.ui import UserInterface

class MonsterMenu(Menu):
    """A class to create monster menu objects. The monster menu allows you to view monsters in
    your party, teach them moves, and switch them both in and out of combat.

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

    >>> monster_menu = MonsterMenu(screen, resolution, self)
    >>> monster_menu.size_x = 200
    >>> monster_menu.size_y = 100
    >>> monster_menu.pos_x = 500
    >>> monster_menu.pos_y = 500
    >>> monster_menu.draw()

    """

    def __init__(self, screen, resolution, game, name="Monster Menu"):

        # Initialize the parent menu class's default shit
        Menu.__init__(self, screen, resolution, name)

        # Give this menu instance access to the main game object.
        self.game = game

        # Set the background color of our menu
        self.color = (32, 104, 96)

        # Load the item menu background image
        _resources = prepare.BASEDIR + "resources/gfx/ui/monster/"
        self.background_image = _resources + "monster_menu_bg.png"
        self.background_surface = pygame.image.load(self.background_image).convert()
        self.background_surface = pygame.transform.scale(self.background_surface,
            (prepare.SCREEN_SIZE[0], prepare.SCREEN_SIZE[1]))


        # Create the item menu's submenus.
        self.active_monster_menu = Menu(screen, resolution, game)
        self.inactive_monsters_menu = Menu(screen, resolution, game)
        self.decision_menu = Menu(screen, resolution, game)
        self.monster_slots = []
        self.monster_hp_bars = []

        # Create a submenu for each monster slot
        from core.components import menu
        for monster_number in range(0, self.game.player1.party_limit):
            self.monster_slots.append(Menu(screen,
                                           resolution,
                                           game,
                                           background=_resources + "filled_monster_slot_bg.png"))
            self.monster_hp_bars.append(menu.interface.HpBar(screen))

        # Set up the border images used for the monster slots
        self.monster_slot_border = {}
        _border_types = ["empty", "filled", "active"]
        _borders = ["left", "right", "top", "bottom", "left-top",
                    "left-bottom", "right-top", "right-bottom", "bg"]
        for border_type in _border_types:
            self.monster_slot_border[border_type] = {}
            for item in _borders:
                img = pygame.image.load(
                    _resources + border_type + "_monster_slot_" + item + ".png").convert()
                self.monster_slot_border[border_type][item] = img

            # Scale the borders according to the game's scale.
            self.monster_slot_border[border_type] = self.scale_borders(
                self.monster_slot_border[border_type])

        # Add the submenus as this menu's children
        self.add_child(self.active_monster_menu)
        self.add_child(self.inactive_monsters_menu)
        self.add_child(self.decision_menu)

        # Set up border images for both inactive and active slots.
        for monster_slot in self.monster_slots:
            self.add_child(monster_slot)

        # Scale the sides of all the submenus
        for menu in self.children:
            # Scale the font and selection arrow to the appropriate size.
            menu.font = pygame.font.Font(
                prepare.BASEDIR + "resources/font/PressStart2P.ttf", menu.font_size * prepare.SCALE)
            menu.arrow = pygame.transform.scale(
                menu.arrow,
                (menu.arrow.get_width() * prepare.SCALE, menu.arrow.get_height() * prepare.SCALE))

            # Scale the window's borders based on the game's scale.
            menu.border = menu.scale_borders(menu.border)

        # Set up our submenus.
        self.decision_menu.size_x = prepare.SCREEN_SIZE[0] / 5
        self.decision_menu.size_y = prepare.SCREEN_SIZE[1] / 6
        self.decision_menu.pos_x = prepare.SCREEN_SIZE[0] - self.decision_menu.size_x - \
            (self.decision_menu.border["left-top"].get_height() * 2)
        self.decision_menu.pos_y = prepare.SCREEN_SIZE[1] - self.decision_menu.size_y - \
            (self.decision_menu.border["left-top"].get_height() * 2)
        self.decision_menu.visible = False
        self.decision_menu.interactable = False

        # Set the positions of our monster slots
        slot_x = (prepare.SCREEN_SIZE[0] / 2) - (self.monster_slots[0].border['left'].get_width() * 2)
        slot_y = (prepare.SCREEN_SIZE[1] / 10)
        for monster_slot in self.monster_slots:
            monster_slot.size_x = int(prepare.SCREEN_SIZE[0] / 2)
            monster_slot.size_y = int(prepare.SCREEN_SIZE[1] /
                (self.game.player1.party_limit * 2 + 2))
            monster_slot.pos_x = slot_x
            monster_slot.pos_y = slot_y

            spacing = int(8 * prepare.SCALE) + monster_slot.size_y
            slot_y += spacing

        self.selected_monster = None

    def draw(self, draw_borders=False, fill_background=False):

        # We can call the draw function from our parent "Menu" class, and also draw
        # some additional stuff specifically for the Monster Menu.
        Menu.draw(self, draw_borders, fill_background)

        # Draw our background image.
        self.screen.blit(self.background_surface, (0,0))

        # Draw our empty monster slots.
        monster_index = 0
        for monster_slot in self.monster_slots:

            # If a monster exists in this slot, populate information about it.
            if monster_index < len(self.game.player1.monsters):
                hp_bar = self.monster_hp_bars[monster_index]
                if monster_index == self.selected_menu_item:
                    monster_slot.border = self.monster_slot_border["active"]
                    monster_slot.background = self.monster_slot_border["active"]["bg"]
                else:
                    monster_slot.border = self.monster_slot_border["filled"]
                    monster_slot.background = self.monster_slot_border["filled"]["bg"]
                monster_slot.draw(fill_background=True)
                monster = self.game.player1.monsters[monster_index]

                # Draw the HP bar
                hp_bar.monster = monster
                hp_bar.x = monster_slot.pos_x + (monster_slot.size_x - hp_bar.surface.get_width())
                hp_bar.y = monster_slot.pos_y + int((hp_bar.height / 2))
                hp_bar.draw()

                # Draw the text on the monster slot
                line_spacing = (monster_slot.font_size * prepare.SCALE) + monster_slot.line_spacing
                monster_slot.draw_text(monster.name)
                monster_slot.draw_text("  Lv " + str(monster.level), pos_y=line_spacing)
            else:
                monster_slot.border = self.monster_slot_border["empty"]
                monster_slot.draw(fill_background=False)

            monster_index += 1

        # Draw the currently active monster
        if len(self.game.player1.monsters) > 0:
            active_monster = self.game.player1.monsters[self.selected_menu_item]
            active_monster.load_sprites(prepare.SCALE)
            active_monster_x = int(prepare.SCREEN_SIZE[0] / 4) - \
                               (active_monster.sprites["front"].get_width() / 2)
            active_monster_y = int(prepare.SCREEN_SIZE[1] / 12)
            active_monster_pos = (active_monster_x, active_monster_y)
            self.screen.blit(active_monster.sprites["front"], active_monster_pos)


    def get_event(self, event, game):

        # Handle when the player presses "ESC".
        if event.type == pygame.KEYDOWN and event.key == prepare.CONFIG.key_menu:

            # If the "ESC" key was pressed while the decision menu was up, close it.
            if self.decision_menu.visible:
                self.decision_menu.visible = False
                self.decision_menu.interactable = False
                self.decision_menu.selected_menu_item = 0
                self.item_list.interactable = True

            # If no other submenus were up when we pressed "ESC", close the monster menu.
            else:
                self.visible = False
                self.interactable = False

                # If the item menu was opened from combat, open up the action menu.
                if game.state_name == "COMBAT":
                    game.state.action_menu.visible = True
                    game.state.action_menu.interactable = True


        elif event.type == pygame.KEYDOWN and event.key == prepare.CONFIG.key_down:

            if self.decision_menu.interactable:
                pass
            else:
                self.selected_menu_item += 1
                if self.selected_menu_item >= len(self.game.player1.monsters):
                    self.selected_menu_item = 0

        elif event.type == pygame.KEYDOWN and event.key == prepare.CONFIG.key_up:

            if self.decision_menu.interactable:
                pass
            else:
                self.selected_menu_item -= 1
                if self.selected_menu_item < 0:
                    if len(self.game.player1.monsters):
                        self.selected_menu_item = len(self.game.player1.monsters) - 1
                    else:
                        self.selected_menu_item = 0

        elif event.type == pygame.KEYDOWN and event.key == prepare.CONFIG.key_action:

            if game.state_name == "COMBAT":
                for player_name, player_dict in self.game.state_dict["COMBAT"].current_players.items():
                    if player_name == 'player':
                        if player_dict['player'].monsters[self.selected_menu_item] == player_dict['monster']:
                            break
                        else:
                            player_dict["action"] = "switch"
                            player_dict["monster"] = player_dict['player'].monsters[self.selected_menu_item]
                            self.game.state_dict["COMBAT"].start_action_phase()
                        break
                    elif player_name == 'opponent':
                        if player_dict['player'].monsters[self.selected_menu_item] == player_dict['monster']:
                            break
                        else:
                            player_dict["action"] = "switch"
                            player_dict["monster"] = player_dict['player'].monsters[self.selected_menu_item]
                            self.game.state_dict["COMBAT"].start_action_phase()
                        break

            elif game.state_name == "WORLD":
                if self.selected_monster is None:
                    self.selected_monster = self.selected_menu_item
                elif self.selected_monster == self.selected_menu_item:
                    self.selected_monster = None
                else:
                    self.game.player1.switch_monsters(self.selected_monster,self.selected_menu_item)
                    self.selected_monster = None

