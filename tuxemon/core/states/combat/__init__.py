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
# Benjamin Bean <superman2k5@gmail.com>
#
#
# core.states.combat Combat Start module
#
#

import logging
import pygame
import math
import os
import sys
import pprint
import time

from core import prepare
from core import state
from core.components import map
from core.components import eztext
from core.components import save
from core.components.ui import bar
from core.components.ui import UserInterface

# Import the android mixer if on the android platform
import core.state

try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("states.combat successfully imported")


class COMBAT(state.State):
    """ The state responsible for all combat related tasks and functions.
    """

    def startup(self, params=None):
        """
        **Monster position drawing**

        We draw the monster's battle sprite on the screen according to the resolution and size of
        the "info_menu":

        >>> self.current_players['player']['monster_sprite']['position'] = (
        ...     0,
        ...     prepare.SCREEN_SIZE[1] - self.info_menu.size_y \
        ...     - self.current_players['player']['monster_sprite']['surface'].get_height()
        ... )

        .. image:: images/combat/monster_drawing01.png

        """
        from core.components import menu

        self.players = params["players"]
        self.combat_type = params["combat_type"]         # Can be either "monster" or "trainer"

        self.current_players = {'player': {}, 'opponent': {}}
        # If we detected the players' health change, we need to animate it.
        self.current_players['player']['health_changed'] = False
        self.current_players['opponent']['health_changed'] = False
        # This is used to pause input from all players while actions are taking place.
        self.turn_in_progress = False
        self.status_check_in_progress = False   # Used to pause input during status check.
        self.status_check_completed = False

        # Keep track of the combat phases
        self.decision_phase = True     # The decision phase allows each player to select an action.
        self.action_phase = False      # The action phase resolves the actions that each player took.
        self.phase = "decision phase"  # The current state of combat.

        # Set up our ui.
        self.ui = {}

        # Use a background color to clear the frame.
        self.background_color = (0,0,0)
        self.text_color = (64,64,64)
        self.ui["background"] = None

        # Create a list of all possible status icons
        self.status_icons = {}
        self.status_icons['Normal'] = pygame.Surface((prepare.ICON_SIZE[0], prepare.ICON_SIZE[1]))
        self.status_icons['Normal'].set_alpha(0)
        self.status_icons['Poisoned'] = pygame.image.load(
            prepare.BASEDIR + 'resources/gfx/ui/icons/status/poison-icon.png').convert_alpha()
        self.status_icons['FNT'] = pygame.Surface((prepare.ICON_SIZE[0], prepare.ICON_SIZE[1]))
        self.status_icons['FNT'].set_alpha(0)

        # Scale all the status icons to the appropriate size based on the game's scale
        for status, surface in self.status_icons.items():
            logger.debug(str(status) + "" + str(surface))
            self.status_icons[status] = pygame.transform.scale(surface,
                (surface.get_width() * prepare.SCALE, surface.get_height() * prepare.SCALE))

        # Load all the party icons to show how many monsters each player has.
        self.party_icons = {}
        self.party_icons['Normal'] = pygame.image.load(
            prepare.BASEDIR + 'resources/gfx/ui/icons/party/party_icon01.png').convert_alpha()
        self.party_icons['Ailment'] = pygame.image.load(
            prepare.BASEDIR + 'resources/gfx/ui/icons/party/party_icon02.png').convert_alpha()
        self.party_icons['FNT'] = pygame.image.load(
            prepare.BASEDIR + 'resources/gfx/ui/icons/party/party_icon03.png').convert_alpha()

        # Scale all the party icons based on the game's scale
        for icon, surface in self.party_icons.items():
            self.party_icons[icon] = pygame.transform.scale(surface,
                (surface.get_width() * prepare.SCALE, surface.get_height() * prepare.SCALE))

        screen = self.game.screen
        game = self.game

        # Bottom info menu
        self.info_menu = menu.Menu(game.screen, prepare.SCREEN_SIZE, game)

        # Action Menu
        self.action_menu = menu.Menu(screen, prepare.SCREEN_SIZE, game)

        # Fight menus
        self.fight_menu = menu.Menu(screen, prepare.SCREEN_SIZE, game)
        self.fight_info_menu = menu.Menu(screen, prepare.SCREEN_SIZE, game)

        # Item menus
        ItemMenu = menu.item_menu.ItemMenu
        self.item_menu = ItemMenu(screen, prepare.SCREEN_SIZE, game)

        # Monster Menu
        MonsterMenu = menu.monster_menu.MonsterMenu
        self.monster_menu = MonsterMenu(screen, prepare.SCREEN_SIZE, game)

        # Active Monster Menu
        #self.active_monster_menu = menu.Menu(screen, prepare.SCREEN_SIZE, game)

        # Inactive Monster Menu
        #self.inactive_monster_menu = menu.Menu(screen, prepare.SCREEN_SIZE, game)

        # Not yet implemented menu
        self.not_implmeneted_menu =  menu.Menu(screen, prepare.SCREEN_SIZE, game)

        # List of all menus
        self.menus = [self.info_menu, self.action_menu, self.fight_menu, self.fight_info_menu,
                      self.monster_menu, #self.active_monster_menu, self.inactive_monster_menu,
                      self.item_menu, self.not_implmeneted_menu]

        # Scale the menu border of all menus
        for menu in self.menus:
            menu.scale = prepare.SCALE
            menu.set_font(size=menu.font_size * menu.scale,
                          font=prepare.BASEDIR + "resources/font/PressStart2P.ttf",
                          color=(10, 10, 10),
                          spacing=menu.font_size * menu.scale)
            menu.arrow = pygame.transform.scale(menu.arrow,
                                                (menu.arrow.get_width() * prepare.SCALE,
                                                 menu.arrow.get_height() * prepare.SCALE))
            for key, border in menu.border.items():
                menu.border[key] = pygame.transform.scale(border,
                    (border.get_width() * prepare.SCALE, border.get_height() * prepare.SCALE))

        # Set the size and pos of windows
        self.info_menu.text = "  "
        self.info_menu.size_x = prepare.SCREEN_SIZE[0] - \
            (self.info_menu.border["left-top"].get_width() * 2)
        self.info_menu.size_y = prepare.SCREEN_SIZE[1] / 6
        self.info_menu.pos_x = (0 + self.info_menu.border["left-top"].get_width())
        self.info_menu.pos_y = prepare.SCREEN_SIZE[1] - \
            (self.info_menu.size_y + (self.info_menu.border["top"].get_height()))

        # Action Menu
        self.action_menu.size_x = prepare.SCREEN_SIZE[0] / 3
        self.action_menu.size_y = prepare.SCREEN_SIZE[1] / 6
        self.action_menu.pos_x = prepare.SCREEN_SIZE[0] - self.action_menu.size_x - \
            self.info_menu.border["left-top"].get_width()
        self.action_menu.pos_y = prepare.SCREEN_SIZE[1] - \
            (self.action_menu.size_y + (self.action_menu.border["top"].get_height()))
        self.action_menu.columns = 2
        self.action_menu.visible = True
        self.action_menu.interactable = True

        # Fight Menu
        self.fight_menu.size_x = prepare.SCREEN_SIZE[0] - self.action_menu.size_x
        self.fight_menu.size_y = prepare.SCREEN_SIZE[1] / 6
        self.fight_menu.pos_x = self.info_menu.pos_x
        self.fight_menu.pos_y = self.info_menu.pos_y
        self.fight_menu.columns = 2
        self.fight_menu.visible = False
        self.fight_menu.interactable = False

        # Fight Info Menu
        self.fight_info_menu.size_x = self.action_menu.size_x
        self.fight_info_menu.size_y = self.action_menu.size_y
        self.fight_info_menu.pos_x = self.action_menu.pos_x
        self.fight_info_menu.pos_y = self.action_menu.pos_y
        self.fight_info_menu.visible = False
        self.fight_info_menu.interactable = False

        # Item Menu
        self.item_menu.size_x = prepare.SCREEN_SIZE[0]
        self.item_menu.size_y = prepare.SCREEN_SIZE[1]
        self.item_menu.pos_x = 0
        self.item_menu.pos_y = 0
        self.item_menu.visible = False
        self.item_menu.interactable = False

        # Monster Menu
        self.monster_menu.size_x = prepare.SCREEN_SIZE[0]
        self.monster_menu.size_y = prepare.SCREEN_SIZE[1]
        self.monster_menu.pos_x = 0
        self.monster_menu.pos_y = 0
        self.monster_menu.visible = False
        self.monster_menu.interactable = False
        #self.monster_menu.add_child(self.active_monster_menu)
        #self.monster_menu.add_child(self.inactive_monster_menu)


        # Active Monster Menu
        #self.active_monster_menu.size_x = prepare.SCREEN_SIZE[0]/3
        #self.active_monster_menu.size_y = prepare.SCREEN_SIZE[1]/2
        #self.active_monster_menu.pos_x = 0
        #self.active_monster_menu.pos_y = 0
        #self.active_monster_menu.visible = False
        #self.active_monster_menu.interactable = False
        #self.active_monster_menu.color = (100, 100, 100)

        # Inactive Monster Menu
        #self.inactive_monster_menu.size_x = (prepare.SCREEN_SIZE[0]/3) * 2
        #self.inactive_monster_menu.size_y = (prepare.SCREEN_SIZE[1]/6) * 5
        #self.inactive_monster_menu.pos_x = prepare.SCREEN_SIZE[0]/3
        #self.inactive_monster_menu.pos_y = 0
        #self.inactive_monster_menu.visible = False
        #self.inactive_monster_menu.interactable = False
        #self.inactive_monster_menu.color = (0, 0, 0)

        # Not yet implemented menu
        self.not_implmeneted_menu.size_x = int(prepare.SCREEN_SIZE[0] / 1.5)
        self.not_implmeneted_menu.size_y = prepare.SCREEN_SIZE[1] / 5
        self.not_implmeneted_menu.pos_x = (prepare.SCREEN_SIZE[0] / 2) - \
            (self.not_implmeneted_menu.size_x / 2)
        self.not_implmeneted_menu.pos_y = (prepare.SCREEN_SIZE[1] / 2) - \
            (self.not_implmeneted_menu.size_y / 2)
        self.not_implmeneted_menu.visible = False
        self.not_implmeneted_menu.interactable = False

        self.player_mon_sprite = None

        # code below was inherited from old Combat.startup

        # Create an alias to our UI dictionary and screen size
        ui = self.ui
        screen_size = prepare.SCREEN_SIZE

        # Load the combat background surface
        ui["background"] = UserInterface(
            prepare.BASEDIR + "resources/gfx/ui/combat/battle_bg02.png", (0, 0), screen)
        ui["background"].scale(screen_size)

        # Loop through all of our players and set up our monsters and UI
        for player_name, player_dict in self.current_players.items():

            # Get the current player object
            if player_name == "player":
                player_dict['player'] = self.players[0]
                player_dict['opponent'] = self.current_players['opponent']
            elif player_name == "opponent":
                player_dict['player'] = self.players[1]
                player_dict['opponent'] = self.current_players['player']

            # Get the player's monster object
            player_dict['monster'] = player_dict['player'].monsters[0]

            # Set the action that the player has decided to do this turn. For example, this
            # action will be set if the player decides to use a move or an item, etc.
            player_dict['action'] = None


            self.load_monster_sprite(ui, screen, screen_size, player_name, player_dict)

            # Set the monster's sprite to visible. They'll turn invisible after the monster's
            # faint animation completes.
            ui[self.player_mon_sprite].visible = True

            # Set the color of the HP bar
            hp_color = (112, 248, 168)

            # Load the battle UI elements such as HP bar, etc.
            player_hp_ui = player_name + "_hp_ui"
            self.ui[player_hp_ui] = UserInterface(
                prepare.BASEDIR + "resources/gfx/ui/combat/hp_%s.png" % player_name,
                (0, 0), screen)

            if player_name == "player":
                # Set up the HP UI background
                ui[player_hp_ui].position = [
                    screen_size[0] - ui[player_hp_ui].width,
                    screen_size[1] - (self.info_menu.size_y + \
                    (self.info_menu.border['top'].get_height() * 2)) - \
                    ui[player_hp_ui].height]
            else:
                # Set up the HP UI background
                ui[player_hp_ui].position = [0, 0]

            # Set the player's technique animation object
            ui['player_technique'] = None
            ui['opponent_technique'] = None

            # The player's health bar starts at pixel position 48,17
            hp_pos = ui[player_hp_ui].position
            if player_name == "player":
                bar_x = hp_pos[0] + (48 * prepare.SCALE)
                bar_y = hp_pos[1] + (17 * prepare.SCALE)
            # The opponent's health bar starts at pixel position 39,17
            else:
                bar_x = hp_pos[0] + (39 * prepare.SCALE)
                bar_y = hp_pos[1] + (17 * prepare.SCALE)

            # Set up the player's health bar
            health_percent = float(player_dict['monster'].current_hp) / \
                float(player_dict['monster'].hp)
            player_hp_bar = player_name + "_healthbar"
            ui[player_hp_bar] = bar.Bar([48, 3],
                                        [bar_x, bar_y],
                                        screen,
                                        color=prepare.HP_COLOR,
                                        value=health_percent * 100)

            # Set up the player's experience bar
            if player_name == "player":
                # The XP bar is at pixel position 32,33 of the health interface
                xp_x = hp_pos[0] + (32 * prepare.SCALE)
                xp_y = hp_pos[1] + (33 * prepare.SCALE)

                # Leveling is based off of total experience, so we need to do a bit of calculation
                # to get the percentage of experience needed for the current level.
                zero_xp = player_dict['monster'].experience_required_modifier * \
                    (player_dict['monster'].level) ** 3
                full_xp = player_dict['monster'].experience_required_modifier * \
                    (player_dict['monster'].level + 1) ** 3
                level_xp = player_dict['monster'].total_experience - zero_xp
                max_xp = full_xp - zero_xp
                # This will give us a percentage of how full the bar should be for this level.
                current_xp = level_xp / float(max_xp)
                logger.info("Current XP: %s / %s" % (level_xp, max_xp))

                # Create our XP bar.
                ui["xp_bar"] = bar.Bar([64, 2],
                                       [xp_x, xp_y],
                                       screen,
                                       color=prepare.XP_COLOR,
                                       value=current_xp * 100)

            # Set up the player's status icon.
            player_status = player_name + "_status"
            ui[player_status] = UserInterface(
                self.status_icons[player_dict['monster'].status],
                (0, 0),
                screen)

            self.set_hp_ui(player_name, player_dict)

            # Load the monster party UI to display the number of monsters a player has in their party.
            # This will only be drawn if the combat is type is "trainer"
            party_bg = player_name + "_party_bg"
            party_bg_image = prepare.BASEDIR + "resources/gfx/ui/combat/party_bg_%s.png" % player_name
            ui[party_bg] = UserInterface(party_bg_image, (0, 0), screen)
            ui[party_bg].state = "open"

            # The "monster_last_hp" is used to detect if damage has been done this frame.
            player_dict['monster_last_hp'] = player_dict['monster'].current_hp


            # Get the position of where we should draw the battle UI elements
            if player_name == "player":

                # Set up the position of the player's status icon for the player
                ui[player_status].position = [
                    ui[player_hp_ui].position[0] + (12 * prepare.SCALE) + \
                    (prepare.ICON_SIZE[0] * prepare.SCALE),
                    ui[player_hp_ui].position[1] + (15 * prepare.SCALE)]
                # Set up the positions of the party UI.
                # Set the UI position when it is opened and visible.
                ui[party_bg].open_position = (
                    ui[player_hp_ui].position[0],
                    ui[player_hp_ui].position[1] - \
                    ui[party_bg].height - (3 * prepare.SCALE))
                # Set the UI position when it is closed and invisible.
                ui[party_bg].closed_position = (
                    ui[party_bg].open_position[0] + \
                    ui[party_bg].width,
                    ui[party_bg].open_position[1])
                # The starting position of the party UI will be open.
                ui[party_bg].position = list(ui[party_bg].open_position)


            elif player_name == "opponent":

                # The opponent's status icon position
                ui[player_status].position = \
                    (3 * prepare.SCALE + (prepare.ICON_SIZE[0] * prepare.SCALE),
                     15 * prepare.SCALE)
                # Set up the position of the party UI.
                # Set the UI position when it is opened and visible.
                ui[party_bg].open_position = (
                    ui[player_hp_ui].position[0],
                    ui[player_hp_ui].position[1] + \
                    ui[player_hp_ui].height + (3 * prepare.SCALE))
                # Set the UI position when it is closed and invisible.
                ui[party_bg].closed_position = (
                    ui[party_bg].open_position[0] - \
                    ui[party_bg].width,
                    ui[party_bg].open_position[1])
                # The starting position of the party UI will be open.
                ui[party_bg].position = list(ui[party_bg].open_position)


        # Set up the capture device animation for use in capturing monsters
        ui["capture"] = UserInterface(
            prepare.BASEDIR + "resources/gfx/items/capture_device.png", (500, 500), screen)
        ui["capture"].visible = False
        import pprint


    def update(self, time_delta):
        player_dict =  self.current_players['player']
        opponent_dict = self.current_players['opponent']
        ui = self.ui

        # If a player has an AI associated with it, execute that AI's decision function
        if opponent_dict['player'].ai and not opponent_dict['action']:
            opponent_dict['action'] = opponent_dict['player'].ai.make_decision(
                opponent_dict,
                player_dict)

        # If both players have selected an action, start the action phase.
        if player_dict['action'] and opponent_dict['action']:
            self.start_action_phase()

        # Handle things that take place during the action phase like health going down, etc.
        if self.action_phase:
            self.action_phase_update()

        #################################################
        #                 UI Animations                 #
        #################################################

        # Set a speed in pixels per second that we'll use for UI animations.
        party_ui_speed = 200 * prepare.SCALE

        # Animate the UI elements for each player if they are animating.
        for player_name, player in self.current_players.items():

            # Don't draw the party UI at all if this is not a trainer battle and this is the opponent
            if self.combat_type != "trainer" and player_name == "opponent":
                continue

        #################################################
        #                   Drawing                     #
        #################################################

        # Update all of our UI elements positions.
        for item in ui:
            if ui[item]:
                ui[item].update(time_delta)


    def draw(self, surface):
        """Draws all combat graphics to the screen including menus, battle sprites, animations, etc.

        :param surface:
        :param game: The main game object that contains all the game's variables.

        :type game: core.control.Control

        :rtype: None
        :returns: None

        """
        game = self.game
        screen = self.game.screen

        # Keep an alias of our UI dictionary
        ui = self.ui

        # Draw the background
        ui["background"].draw()

        # Draw the actual monster sprites
        for player_name, player in self.current_players.items():
            ui[player_name + '_monster_sprite'].draw()

        for player_name, player in self.current_players.items():
            # Draw technique animations
            if ui[player_name + '_technique']:
                ui[player_name + '_technique'].draw()

        # Draw the capture device animation
        ui['capture'].draw()

        # Draw the menus
        self.info_menu.draw()
        self.info_menu.draw_text(self.info_menu.text, justify="center", align="middle")
        if self.info_menu.elapsed_time <= self.info_menu.delay:
            self.info_menu.elapsed_time += game.time_passed_seconds # Keep track of how long this window has been open

        if self.action_menu.visible:
            self.action_menu.draw()
            self.action_menu.draw_textItem(["Fight", "Item", "Tuxemon", "Run"], columns=2, autoline_spacing=True)

        if self.fight_menu.visible:
            available_moves = []

            # Get the names of the techniques this monster can use.
            for move in self.current_players['player']['monster'].moves:
                available_moves.append(move.name)

            self.fight_menu.draw()
            self.fight_menu.draw_textItem(available_moves, columns=2, autoline_spacing=True)
            self.fight_info_menu.draw()

        # Draw the UI elements
        for player_name, player in self.current_players.items():
            ui[player_name + "_hp_ui"].draw()
            party_ui = ui[player_name + "_party_bg"]

            # If this is not a trainer battle, don't draw the opponent's party UI
            if self.combat_type != "trainer" and player_name == "opponent":
                party_ui.visible = False

            # Draw the player's party if this is a trainer battle.
            if party_ui.visible:
                party_ui.draw()

                # Keep track of which monster icon we're going to draw.
                monster_number = 0

                # Space each icon by 10 pixels
                icon_spacing = 10 * prepare.SCALE

                # Start drawing the icons at (26, 0) on the party ui background
                icon_starting_pos = 26 * prepare.SCALE

                # Draw the player's party to show how many monsters the player has remaining.
                for monster in player['player'].monsters:
                    party_icon_position = (party_ui.position[0] + icon_starting_pos +
                        (monster_number * icon_spacing), party_ui.position[1])

                    # Draw the party icon based on the monster's status.
                    if monster.status == "Normal":
                        party_icon_surface = self.party_icons['Normal']
                    elif monster.status == "FNT":
                        party_icon_surface = self.party_icons['FNT']
                    else:
                        party_icon_surface = self.party_icons['Ailment']

                    screen.blit(party_icon_surface, party_icon_position)

                    monster_number += 1

            # Draw the monsters' level and name
            ui[player_name + "_lvl_text"].draw()
            ui[player_name + "_monster_name"].draw()

        # Draw the monsters' health
        for player_name, player in self.current_players.items():
            ui[player_name + "_healthbar"].draw()
        ui["xp_bar"].draw()

        # Draw Monster Menu
        if self.monster_menu.visible:
            self.monster_menu.draw(draw_borders=False)

        # Draw Active Monster Menu
        #if self.active_monster_menu.visible:
        #    self.active_monster_menu.draw(draw_borders=True)

        # Draw Inactive Monster Menu
        #if self.inactive_monster_menu.visible:
        #    self.inactive_monster_menu.draw(draw_borders=True)

        # Draw the Item Menu
        if self.item_menu.visible:
            self.item_menu.draw(draw_borders=False)

        # Draw the not yet implemented menu to let the player know when shit ain't
        # workin' yet
        if self.not_implmeneted_menu.visible:
            self.not_implmeneted_menu.draw()
            self.not_implmeneted_menu.draw_text("This feature is not yet implemented.",
                justify="center", align="middle")


    def animate_health(self, player):
        """Animates changes in health for monsters in combat. The speed of the animation is based
        on HP change per second. Returns the percentage of health remaining.

        :param None:

        :rtype: Float
        :returns: A float of the percentage of health remaining for the monster.

        """

        # Set how quickly the health will change in HP points per second
        hp_per_second = 10

        # Set some aliases
        current_player = self.current_players[player]
        game = self.game

        # Start adding or subtracting hp until we reach our target value.
        if current_player['target_health'] < current_player['starting_health']:
            current_player['starting_health'] -= hp_per_second * game.time_passed_seconds
        elif current_player['target_health'] > current_player['starting_health']:
            current_player['starting_health'] += hp_per_second * game.time_passed_seconds

        # If we've reached our target health value, then stop animating by setting "health_changed" = False.
        if current_player['health_changed'] == "down":
            if current_player['starting_health'] <= current_player['target_health']:
                current_player['health_changed'] = False
                current_player['starting_health'] = current_player['target_health']

        elif current_player['health_changed'] == "up":
            if current_player['starting_health'] >= current_player['target_health']:
                current_player['health_changed'] = False
                current_player['starting_health'] = current_player['target_health']


        # Set the size of health bar based on how much health the monster has remaining.
        if current_player['starting_health'] > 0:
            health_percent = float(current_player['starting_health']) / float(current_player['monster'].hp)
        elif current_player['starting_health'] > current_player['monster'].hp:
            health_percent = 1.0
        else:
            health_percent = 0

        return health_percent


    def get_event(self, event):
        """Handles player input events when combat has been initiated. Directs all player input to
        battle menus, etc.

        :param game: The main game object that contains all the game's variables.

        :type game: core.control.Control

        :rtype: None
        :returns: None

        """
        game = self.game

        # Handle menu events

        # If the not implemented window is open, send pygame events to it.
        if self.not_implmeneted_menu.interactable:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.not_implmeneted_menu.visible = False
                self.not_implmeneted_menu.interactable = False

            # Don't process any other input until the user presses ENTER.
            return False

        if self.action_menu.interactable:
            self.action_menu.update_menu_selection(event)

        if self.fight_menu.interactable:
            self.fight_menu.update_menu_selection(event)

        if self.item_menu.interactable:
            self.item_menu.get_event(event, game)

        if self.monster_menu.interactable:
            self.monster_menu.get_event(event, game)


        # Handle key inputs.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.fight_menu.visible:
                self.fight_menu.visible = False
                self.fight_menu.interactable = False

                self.action_menu.visible = True
                self.action_menu.interactable = True


        # If the player presses Enter while a menu item is selected
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:

            ### Action Menu Events ###
            if self.action_menu.interactable:

                # If we selected the "Fight" option, then open the fight menu.
                if self.action_menu.selected_menu_item == 0:
                    self.fight_menu.visible = True
                    self.fight_menu.interactable = True
                    self.fight_info_menu.visible = True

                    self.action_menu.visible = False
                    self.action_menu.interactable = False

                # If "Item" was selected, open the item menu
                elif self.action_menu.selected_menu_item == 1:
                    logger.info("Opening Item menu!")
                    self.item_menu.visible = True
                    self.item_menu.interactable = True
                    self.item_menu.state = "open"
                    self.action_menu.visible = False
                    self.action_menu.interactable = False

                # If "Tuxemon" was selected, open the tuxemon menu
                elif self.action_menu.selected_menu_item == 2:
                    logger.info("Tuxemon menu!")
                    #self.not_implmeneted_menu.visible = True
                    #self.not_implmeneted_menu.interactable = True
                    self.monster_menu.visible = True
                    self.monster_menu.interactable = True
                    self.monster_menu.state = "open"
                    self.action_menu.visible = False
                    self.action_menu.interactable = False

                # If "Run" was selected, try and run away
                elif self.action_menu.selected_menu_item == 3:
                    logger.info("Run away!")

                    # Exit combat for now. In the future, we'll check for trainer battle and do a
                    # roll, etc.
                    self.end_combat()

            ### Fight Menu Events ###
            elif self.fight_menu.interactable:

                # Use the selected move against the opponent
                selected_move = self.fight_menu.selected_menu_item
                # Set the player's action to use a technique this turn.
                self.current_players['player']['action'] = {'technique': selected_move}


    def start_decision_phase(self):
        """Once actions have been completed, this function will re-enable player input to allow the
        player to make a new decision.

        :param None:

        :rtype: None
        :returns: None

        """

        # Make the action menu and info menus visible and interactable.
        self.action_menu.interactable = True
        self.action_menu.visible = True
        self.info_menu.visible = True
        self.info_menu.text = "  "
        self.info_menu.elapsed_time = self.info_menu.delay  # Reset the window delay

        # Open the party UI during the decision phase.
        for player_name, player in self.current_players.items():
            party_ui = self.ui[player_name + '_party_bg']
            party_ui.move(party_ui.open_position, 0.5)

        # Set the monsters' status icon to reflect their current status. For example, if
        # the monster was poisoned, this will set their status icon to the poison icon.
        for player_name, player_dict in self.current_players.items():
            self.ui[player_name + "_status"].surface = \
                self.status_icons[player_dict['monster'].status]

        # End the action phase and start the decision phase.
        self.action_phase = False
        self.decision_phase = True
        self.phase = "decision phase"


    def start_action_phase(self):
        """After both players have input an action, this function will pause all player input and
        perform the selected actions of each player.

        :param None:

        :rtype: None
        :returns: None

        """

        # This will be executed when both players have selected an action.
        self.action_phase = True
        self.decision_phase = False
        self.phase = "action phase"
        players = self.current_players

        # Create a list of players ordered by who will go first.
        self.turn_order = []

        # Disable all menus while the action phase is in progress
        for menu in self.menus:
            menu.interactable = False
            menu.visible = False

        # Close the party UI during the action phase.
        for player_name, player in self.current_players.items():
            party_ui = self.ui[player_name + '_party_bg']
            party_ui.move(party_ui.closed_position, 0.5)
            print("Closed position for " + player_name + ":", party_ui.closed_position)

        # Determine which monster goes first based on the speed of the monsters.
        if players['player']['monster'].speed >= players['opponent']['monster'].speed:
            self.turn_order.append(players['player'])
            self.turn_order.append(players['opponent'])
        else:
            self.turn_order.append(players['opponent'])
            self.turn_order.append(players['player'])


    def action_phase_update(self):
        """Updates the game every frame during the action phase.
        """
        # Create an alias for our UI data structure.
        ui = self.ui

        # If we're in the action phase, but an action is not actively being carried out, start
        # the next player's action.
        if not self.turn_in_progress:
            self.start_turn()

        # If an action IS actively being carried out, draw the animations for the action.
        else:
            self.turn_update()

        # If all turns have been taken, start the decision phase.
        if len(self.turn_order) == 0:
            self.start_decision_phase()


    def start_turn(self):
        """Starts a turn for a monster during the action phase.
        """
        logger.info("")
        logger.info("Starting turn for " + self.turn_order[0]['player'].name)
        if not self.status_check_in_progress and not self.status_check_completed:
            logger.info("  Performing status check and resolving damage from status.")
            self.status_check(self.turn_order[0])
            self.status_check_in_progress = True
            self.status_check_completed = False
            self.phase = "status check in progress"

        # We want to perform our action AFTER the status check has completed.
        elif self.status_check_completed:
            logger.info("  Status check completed. Performing action.")
            self.perform_action(self.turn_order[0])
            self.status_check_in_progress = False
            self.status_check_completed = False

        self.turn_in_progress = True


    def turn_update(self):
        """Updates every frame to carry out a monster's turn during the action phase.
        """
        ##############################################
        #               Health Animations            #
        ##############################################
        game = self.game
        ui = self.ui
        players = self.current_players

        # If a monster has taken damage this frame, then start animating the health.
        for player_name, player in players.items():
            if player['monster_last_hp'] != player['monster'].current_hp:
                game.rumble.rumble(-1, length=1)
                logger.info("Player Health Change: " + str(player['monster_last_hp']) +
                    " -> " + str(player['monster'].current_hp))

                players[player_name]['starting_health'] = player['monster_last_hp']
                players[player_name]['target_health'] = player['monster'].current_hp

                # Indicate that this monster's health has changed and in which direction it has been changed. Was
                # the monster damaged or healed?
                if player['monster_last_hp'] < player['monster'].current_hp:
                    players[player_name]['health_changed'] = "up"
                else:
                    players[player_name]['health_changed'] = "down"

                # Set the last HP value to the current one so we don't execute this function endlessly
                players[player_name]['monster_last_hp'] = player['monster'].current_hp

            # If we're in the middle of animating health change, then calculate the percentage of health left and
            # transform the health bar based on that percentage.
            if player['health_changed']:
                health_percent = self.animate_health(player_name) * 100
                ui[player_name + '_healthbar'].value = health_percent

                logger.debug("  Animating player health: " + str(health_percent))


            ########################################################
            #                  Fainting Animations                 #
            ########################################################

            # If the monster is fainting, play the fainting animation and remove the monster.
            if player['monster'].state == "fainting" and not player['health_changed']:
                monster_sprite = ui[player_name + "_monster_sprite"]
                monster_sprite.move(monster_sprite.faint_position, 0.5)

                # If the sprite's position has reached the fainting position, make the
                # sprite invisible and set the state to "fainted"
                if monster_sprite.position[1] >= monster_sprite.faint_position[1]:
                    players[player_name]['monster'].state = "fainted"
                    monster_sprite.visible = False

                    # Play the sound of their HORRIBLE DEATH
                    sound = mixer.Sound(prepare.BASEDIR + "resources/sounds/monster/1/faint.ogg")
                    sound.play()

                    # Award experience to player if opponent's monster fainted
                    if player_name == "opponent":
                        # Aliases to make referencing monsters more concise
                        player_monster = players['player']['monster']
                        opponent_monster = players['opponent']['monster']
                        # Give player's monster experience for faint of opponent monster
                        xp = (opponent_monster.experience_give_modifier * opponent_monster.level) ** 3
                        player_monster.give_experience(xp)
                        logger.info("Monster gained experience: %i" % xp)

                    # Check to see if the player has any more remaining monsters in their
                    # party that haven't fainted.
                    alive_monster_found = False
                    for monster in player['player'].monsters:
                        if monster.status != "FNT":
                            alive_monster_found = True

                    if alive_monster_found:
                        logger.warning("Let the player choose his next monster!")

                    else:
                        if player_name == "player":
                            logger.info("YOU LOST!")
                            self.info_menu.text = "YOU LOST!"
                            self.info_menu.elapsed_time = 0.0
                            self.phase = "lost"

                        elif player_name == "opponent":
                            logger.info("YOU WON!")
                            self.info_menu.text = "YOU WON!"
                            self.info_menu.elapsed_time = 0.0
                            self.phase = "won"

            ########################################################
            #                  Creature Capturing                  #
            ########################################################

        if ("capturing" in self.phase) and self.info_menu.elapsed_time > self.info_menu.delay:

            if self.phase == "capturing success":
                print("Capturing %s!!!" % players['opponent']['monster'].name)
                self.info_menu.text = "You captured %s!" % players['opponent']['monster'].name
                self.info_menu.elapsed_time = 0.0
                self.phase = "captured"
            elif self.phase == "capturing fail":
                print("Could not capture %s!" % players['opponent']['monster'].name)
                self.info_menu.text = "%s broke free!" % players['opponent']['monster'].name
                self.info_menu.elapsed_time = 0.0
                ui["capture"].visible = False
                self.phase = "action phase"

        # Handle when all monsters in the player's party have fainted
        if (self.phase == "lost" or self.phase == "won" or self.phase == "captured") and self.info_menu.elapsed_time > self.info_menu.delay:
            self.end_combat()


        #######################################################
        #                   Finish turn                       #
        #######################################################

        # Stop this turn once the health animations have stopped and the appropriate amount
        # of time has passed for the info menu.
        if (not players['player']['health_changed']
            and not players['opponent']['health_changed']
            and self.info_menu.elapsed_time > self.info_menu.delay
            and (players['player']['monster'].state != "fainting" or players['opponent']['monster'].state != "fainting")):
            self.turn_in_progress = False

            if self.status_check_in_progress:
                self.status_check_completed = True
                self.phase = "status check completed"

            # If this isn't part of a status check, end the turn for the current player.
            else:
                self.turn_order.pop(0)      # Remove the player from the turn list.

        #elif self.info_menu.elapsed_time < self.info_menu.delay:
        #    print("  Waiting %f seconds for window delay" % (self.info_menu.delay - self.info_menu.elapsed_time))


    def perform_action(self, player):
        """Perform an action that a single player has decided on. Players can decide to use a
        technique, item, switch monsters, or run away.

        :param player: The player object dictionary that is performing the action.

        :type player: Dictionary

        :rtype: None
        :returns: None

        **Example:**

        A player object dictionary contains a player object and meta-information about that player
        object such as the player's decision, current monster, etc. This is what a player object
        dictionary looks like:

        >>> player
        {'action': None,
         'monster': <monster.Monster instance at 0x7f9d80733a70>,
         'monster_last_hp': 30,
         'monster_level_text': {'font': <pygame.font.Font object at 0x7f9d8094b290>,
                                'position': (1210, 385),
                                'surface': <Surface(35x36x32 SW)>},
         'monster_sprite': {'position': (0, 280), 'surface': <Surface(320x320x32 SW)>},
         'player': <player.Player instance at 0x7f9d80977c20>}

        """
        game = self.game
        screen = self.game.screen

        # If the player selected a technique, use the selected technique on the opposing monster.
        if 'technique' in player['action']:

            # Get the monster's last hp value before the damage is done
            player['monster_last_hp'] = player['monster'].current_hp
            player['opponent']['monster_last_hp'] = player['opponent']['monster'].current_hp

            # Get the move that the player decided to use.
            selected_move = player['action']['technique']
            player['monster'].moves[selected_move].use(
                user=player['monster'], target=player['opponent']['monster'])

            # Display a dialog showing that we used a move
            self.info_menu.text = "%s used %s!" % (player['monster'].name,
                                                   player['monster'].moves[selected_move].name)
            self.info_menu.elapsed_time = 0.0

            logger.info("Using " + player['monster'].moves[selected_move].name)
            logger.info("Level: " + str(player['monster'].level))
            logger.info("")
            logger.info("Player monster HP: " + str(player['monster'].current_hp))
            logger.info("Opponent monster HP: " + str(player['opponent']['monster'].current_hp))

            # If using this technique kills either the player's monster OR the opponent's
            # monster, set their status to FUCKING DEAD.
            if player['opponent']['monster'].current_hp <= 0:
                player['opponent']['monster'].current_hp = 0
                player['opponent']['monster'].status = 'FNT'
                player['opponent']['monster'].state = "fainting"

            if player['monster'].current_hp <= 0:
                player['monster'].current_hp = 0
                player['monster'].status = 'FNT'
                player['monster'].state = "fainting"

            # Make a tackle animation when a technique is used.
            if player is self.current_players['player']:
                monster_sprite = self.ui['player_monster_sprite']
                tackle_delta = (10 * prepare.SCALE)

                # Play the animation of the technique
                images = player['monster'].moves[selected_move].images
                self.ui['player_technique'] = UserInterface(images,
                                                            self.ui['opponent_monster_sprite'].position,
                                                            screen,
                                                            animation_speed=0.1)
                self.ui['player_technique'].play()

            else:
                monster_sprite = self.ui['opponent_monster_sprite']
                tackle_delta = -(10 * prepare.SCALE)

                # Play the animation of the technique
                images = player['monster'].moves[selected_move].images
                self.ui['opponent_technique'] = UserInterface(images,
                                                            self.ui['player_monster_sprite'].position,
                                                            screen,
                                                            animation_speed=0.1)
                self.ui['opponent_technique'].play()

            tackle_destination = (monster_sprite.position[0] + tackle_delta,
                                  monster_sprite.position[1])
            monster_sprite.shake_once(tackle_destination, duration=0.2)
            monster_sprite.tackled = True

            # Play the technique's sound effect.
            sound = mixer.Sound(player['monster'].moves[selected_move].sfx)
            sound.play()

        # If the player selected to use an item, use the item.
        elif 'item' in player['action']:

            # Get the monster's last hp value before the item is used, so we can animate
            # their health in the main update loop.
            player['monster_last_hp'] = player['monster'].current_hp
            player['opponent']['monster_last_hp'] = player['opponent']['monster'].current_hp

            # Get the item object from the player's inventory that the player decided to use
            # and USE IT.
            item_name = player['action']['item']['name']
            item_target = player['action']['item']['target']
            item_to_use = player['player'].inventory[item_name]['item']

            # Use item and change game state if captured or not
            if "capture" in item_to_use.effect:
                self.ui["capture"].visible = True
                self.ui["capture"].move(self.ui["opponent_monster_sprite"].position, 1.)
                if item_to_use.capture(item_target, game):
                    self.phase = "capturing success"
                else:
                    self.phase = "capturing fail"
            else:
                item_to_use.use(item_target, game)


            # Display a dialog showing that we used an item
            self.info_menu.text = "%s used %s on %s!" % (player['player'].name,
                item_name, item_target.name)

            # Set the info menu timer to zero, so the menu will display for a short period of
            # time.
            self.info_menu.elapsed_time = 0.0

            logger.info("Using item!")

        elif 'switch' in player['action']:
            for player_name, player_dict in self.current_players.items():
                if player_dict['player'] == self.current_players['player']['player']:

                    # Display switch message
                    self.info_menu.text = "Go %s!" % (player['monster'].name)

                    # Load new Tuxemon sprite
                    self.load_monster_sprite(self.ui, screen, prepare.SCREEN_SIZE, player_name, player_dict)

                    # Set new Tuxemon hp, name, and level
                    self.set_hp_ui(player_name, player_dict)

                    # Set the info menu timer to zero, so the menu will display for a short period of
                    # time.
                    self.info_menu.elapsed_time = 0.0

                    # We're not the other player, so stop here
                    break
                elif player_dict['player'] == self.current_players['opponent']['player']:

                    # Display switch message
                    self.info_menu.text = "%s sent out %s!" % (player_name, player['monster'].name)

                    # Load new Tuxemon sprite
                    self.load_monster_sprite(self.ui, screen, prepare.SCREEN_SIZE, player_name, player_dict)

                    # Set new Tuxemon hp, name, and level
                    self.set_hp_ui(player_name, player_dict)

                    # Set the info menu timer to zero, so the menu will display for a short period of
                    # time.
                    self.info_menu.elapsed_time = 0.0

                    # We're not the other player, so stop here
                    break

        # Remove the player's current decision in preparation for the next turn.
        player['action'] = None


    def status_check(self, player):
        """This method checks to see if a given player's currently active monster has any status
        effects (such as poison, paralyze, etc.) and resolves those effects. So if a monster was
        poisoned, executing this method will make that monster take poison damage. It also sets
        how much damage the monster took so we can animate their health going down in the update
        loop.

        :param player: The player object dictionary that we're checking the status for.

        :type player: Dictionary

        :rtype: None
        :returns: None

        **Example:**

        A player object dictionary contains a player object and meta-information about that player
        object such as the player's decision, current monster, etc. This is what a player object
        dictionary looks like:

        >>> player
        {'action': None,
         'monster': <monster.Monster instance at 0x7f9d80733a70>,
         'monster_last_hp': 30,
         'monster_level_text': {'font': <pygame.font.Font object at 0x7f9d8094b290>,
                                'position': (1210, 385),
                                'surface': <Surface(35x36x32 SW)>},
         'monster_sprite': {'position': (0, 280), 'surface': <Surface(320x320x32 SW)>},
         'player': <player.Player instance at 0x7f9d80977c20>}

        """

        logger.info('Checking Status for ' + player['player'].name)
        logger.info('  Monster Status: ' + player['monster'].status)

        # Get the monster's hp before resolving damage from status effects.
        player['monster_last_hp'] = player['monster'].current_hp

        # If the player's monster was poisoned, make the monster take poison damage.
        if player['monster'].status == 'Poisoned':

            # Only take poison damage if we've been poisoned for longer than 1 turn.
            if player['monster'].status_turn >= 1:
                logger.info("  This monster is taking poison damage this turn.")
                self.info_menu.text = "%s took poison damage!" % player['monster'].name
                self.info_menu.elapsed_time = 0.0
                player['monster_last_hp'] = player['monster'].current_hp
                player['monster'].current_hp -= 10

            # Keep track of how many turns this monster has been poisoned.
            player['monster'].status_turn += 1

        # If the player's HP drops below zero due to status effects, set them fainting.
        # Then we can animate the monster fainting based on this variable.
        if player['monster'].current_hp <= 0:
            player['monster'].status = 'FNT'
            player['monster'].state = "fainting"


    def load_monster_sprite(self, ui, screen, screen_size, player_name, player_dict):
            """Loads a monster sprite

            :param ui: The dictionary that contains all UI objects for the combat state.
            :param screen: The pygame screen object to draw to.
            :param screen_size: The size of the current screen.
            :param player_name: The name of the player.
            :param player_dict: The player's dictionary that contains the player's active monster.

            :type ui: Dictionary
            :type screen: pygame.screen
            :type screen_size: Tuple
            :type player_name: String
            :type player_dict: Dictionary

            :rtype: None
            :returns: None

            **Example:**

            """

            if player_name == "player":
                monster_sprite = player_dict['monster'].back_battle_sprite
            elif player_name == "opponent":
                monster_sprite = player_dict['monster'].front_battle_sprite

            self.player_mon_sprite = player_name + '_monster_sprite'
            ui[self.player_mon_sprite] = UserInterface(monster_sprite, (0, 0), screen)

            if player_name == "player":
                ui[self.player_mon_sprite].position = [
                    (screen_size[0] / 7),
                    screen_size[1] - self.info_menu.size_y - \
                    ui[self.player_mon_sprite].height]
            elif player_name == "opponent":
                ui[self.player_mon_sprite].position = [
                    screen_size[0] - ui[self.player_mon_sprite].width - \
                    (screen_size[0] / 7),
                    (screen_size[1] / 8)]

            ui[self.player_mon_sprite].faint_position = \
                (ui[self.player_mon_sprite].position[0],
                ui[self.player_mon_sprite].position[1] + \
                ui[self.player_mon_sprite].height)

            ui[self.player_mon_sprite].visible = True


    def set_hp_ui(self, player_name, player_dict):

        screen = self.game.screen
        player_hp_ui = player_name + "_hp_ui"

        # Set Tuxemon hp bar
        player_dict['monster_last_hp'] = player_dict['monster'].current_hp
        player_dict['starting_health'] = player_dict['monster'].current_hp
        player_dict['target_health'] = player_dict['monster'].current_hp
        health_percent = self.animate_health(player_name) * 100
        self.ui[player_name + '_healthbar'].value = health_percent

        # Set Tuxemon level text
        lvl_font = pygame.font.Font(prepare.BASEDIR + "resources/font/PressStart2P.ttf", 7 * prepare.SCALE)
        lvl_text = lvl_font.render(str(player_dict['monster'].level),
                            1, self.text_color)
        self.ui[player_name + '_lvl_text'] = UserInterface(lvl_text, (0, 0), screen, scale=False)

        # The Tuxemon level text position
        self.ui[player_name + '_lvl_text'].position = (
        self.ui[player_hp_ui].position[0] + \
        self.ui[player_hp_ui].width - (18 * prepare.SCALE),
        self.ui[player_hp_ui].position[1] + (6 * prepare.SCALE))

        # Set Tuxemon name text
        player_mon_name = player_name + "_monster_name"
        monster_text = lvl_font.render(str(player_dict['monster'].name),
                                1,
                                self.text_color)
        self.ui[player_mon_name] = UserInterface(monster_text, (0, 0), screen, scale=False)

        # Set Tuxemon name text position
        self.ui[player_mon_name].position = [
        self.ui[player_hp_ui].position[0] + (14 * prepare.SCALE),
        self.ui[player_hp_ui].position[1] + (6 * prepare.SCALE)]

    def end_combat(self):
        # TODO: End combat differently depending on winning or losing
        event_engine = self.game.event_engine
        event_engine.actions["fadeout_music"]["method"](self.game, [None, 1000])

        # TODO: remove this fade-in hack when proper transition is complete
        world = self.game.get_state_name("world")
        world.trigger_fade_in()

        self.game.pop_state()
        self.game.push_state("FADE_OUT_TRANSITION")


if __name__ == "__main__":

    print("Runs as standalone")

    from core.components import config

    class Game(object):

        def __init__(self):
            # set up pygame
            pygame.init()
            # read the configuration file
            self.config = config.Config()
            # The game resolution
            self.resolution = self.config.resolution
            # set up the window
            self.screen = pygame.display.set_mode(self.resolution, self.config.fullscreen, 32)
            pygame.display.set_caption('Tuxemon Combat System')
            # Create a clock object that will keep track of how much time has passed since the last frame
            self.clock = pygame.time.Clock()
            # Set the font for the FPS and other shit
            self.font = pygame.font.Font(prepare.BASEDIR + "resources/font/PressStart2P.ttf", 14)

            # Native resolution is similar to the old gameboy resolution. This is used for scaling.
            self.native_resolution = [240, 160]

            # If scaling is enabled, set the scaling based on resolution
            if self.config.scaling == "1":
                self.scale = int( (self.resolution[0] / self.native_resolution[0]) )
            else:
                self.scale = 1

            self.combat = COMBAT(self)

            while True:
                self.clock.tick()
                self.screen.fill((0,0,0))
                self.events = pygame.event.get()

                for event in self.events:
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    # Exit the game if you press ESC
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                self.combat.draw()
                self.combat.handle_events(self)

                # Calculate the FPS and print it onscreen for debugging purposes
                fps = self.font.draw("FPS: " + str(self.clock.get_fps()), 1, (240, 240, 240))
                self.screen.blit(fps, (10, 10))

                pygame.display.flip()



    Game()
