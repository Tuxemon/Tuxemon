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
# Leif Theden <leif.theden@gmail.com>
#
#
# core.states.combat Combat Start module
#
#
from __future__ import division

import logging
from collections import namedtuple, defaultdict
from functools import partial
from operator import attrgetter
from random import choice

import pygame

from core import tools
from core.components.monster import Technique
from core.components.pyganim import PygAnimation
from core.components.sprite import Sprite
from core.components.ui.draw import GraphicBox
from core.components.ui.text import TextArea
from .combat_animations import CombatAnimations

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

EnqueuedAction = namedtuple("EnqueuedAction", "user technique target")


faint = Technique("Faint")


def check_status(monster, status_name):
    return any(t for t in monster.status if t.name == status_name)


def fainted(monster):
    return check_status(monster, "Faint")


def get_awake_monsters(player):
    """ Iterate all non-fainted monsters in party

    :param player:
    :return:
    """
    for monster in player.monsters:
        if not fainted(monster):
            yield monster


def fainted_party(party):
    return all(map(fainted, party))


def defeated(player):
    return fainted_party(player.monsters)


class CombatState(CombatAnimations):
    """ The state-menu responsible for all combat related tasks and functions.
        .. image:: images/combat/monster_drawing01.png
    """
    background_filename = "gfx/ui/combat/battle_bg03.png"
    draw_borders = False
    escape_key_exits = False

    def startup(self, **kwargs):
        self.max_positions = 1  # TODO: make dependant on match type
        self.phase = None
        self.monsters_in_play = defaultdict(list)
        self._experience_tracking = defaultdict(list)
        self._technique_cache = dict()       # cache for technique animations
        self._decision_queue = list()        # queue for monsters that need decisions
        self._position_queue = list()        # queue for asking players to add a monster into play (subject to change)
        self._action_queue = list()          # queue for techniques, items, and status effects
        self._monster_sprite_map = dict()    # monster => sprite
        self._hp_bars = dict()               # monster => hp bar
        self._layout = dict()                # player => home areas on screen
        self._animation_in_progress = False  # if true, delay phase change
        self._winner = None                  # when set, combat ends
        self._round = 0

        super(CombatState, self).startup(**kwargs)
        self.players = list(self.players)
        self.show_combat_dialog()
        self.transition_phase("begin")
        self.task(partial(setattr, self, "phase", "ready"), 3)

    def update(self, time_delta):
        super(CombatState, self).update(time_delta)
        if not self._animation_in_progress:
            new_phase = self.determine_phase(self.phase)
            if new_phase:
                self.phase = new_phase
                self.transition_phase(new_phase)
            self.update_phase()

    def draw(self, surface):
        super(CombatState, self).draw(surface)
        self.draw_hp_bars()

    def draw_hp_bars(self):
        """ Go through the HP bars and redraw them

        :returns: None
        """
        for monster, hud in self.hud.items():
            rect = pygame.Rect(0, 0, tools.scale(70), tools.scale(8))
            rect.right = hud.image.get_width() - tools.scale(8)
            rect.top += tools.scale(12)
            self._hp_bars[monster].draw(hud.image, rect)

    def determine_phase(self, phase):
        """ Determine the next phase and set it

        Only test and set new phase.  Do not execute phase actions.

        :returns: None
        """
        if phase == "ready":
            return "housekeeping phase"

        elif phase == "housekeeping phase":
            return "decision phase"

        elif phase == "decision phase":
            if len(self._action_queue) == len(list(self.active_monsters)):
                return "pre action phase"

            # if a player runs, it will be known here
            self.check_match_status()
            if self._winner:
                return "resolve match"

        elif phase == "pre action phase":
            return "action phase"

        if phase == "action phase":
            if not self._action_queue:
                return "post action phase"

        elif phase == "post action phase":
            if not self._action_queue:
                return "ready"

        elif phase == "resolve match":
            if not self._winner:
                return "housekeeping phase"

    def transition_phase(self, phase):
        """ Change from one phase from another.

        This will be run just once when phase changes.
        Do not change phase.  Just runs actions for new phase.

        :param phase:
        :return:
        """
        if phase == "housekeeping phase":
            self._round += 1
            self.fill_battlefield_positions(ask=self._round > 1)

        if phase == "decision phase":
            if not self._decision_queue:
                for player in self.human_players:
                    self._decision_queue.extend(self.monsters_in_play[player])

                for trainer in self.ai_players:
                    for monster in self.monsters_in_play[trainer]:
                        # TODO: real ai...
                        target = choice(self.monsters_in_play[self.players[0]])
                        self.enqueue_action(monster, choice(monster.moves), target)

        elif phase == "action phase":
            self._action_queue.sort(key=attrgetter("user.speed"))

        elif phase == "post action phase":
            for monster in self.active_monsters:
                for technique in monster.status:
                    self.enqueue_action(None, technique, monster)

        elif phase == "resolve match":
            self.check_match_status()
            if self._winner:
                self.end_combat()

    def update_phase(self):
        """ Execute/update phase actions

        Do not change phase.  This will be run each iteration phase is active.
        Do not test conditions to change phase.  Only do actions.

        :return: None
        """
        if self.phase == "decision phase":
            if self._decision_queue:
                monster = self._decision_queue.pop()
                self.show_monster_action_menu(monster)

        elif self.phase == "action phase":
            self.handle_action_queue()

        elif self.phase == "post action phase":
            self.handle_action_queue()

    def handle_action_queue(self):
        """ Take one action from the queue and do it

        :return: None
        """
        if self._action_queue:
            action = self._action_queue.pop()
            self.perform_action(*action)
            self.check_party_hp()
            self.task(self.animate_party_status, 3)

    def ask_player_for_monster(self, player):
        """ Open dialog to allow player to choose a TXMN to enter into play

        :param player:
        :return:
        """
        def add(menuitem):
            monster = menuitem.game_object

            if monster.current_hp == 0:
                tools.open_dialog(self.game, ["Cannot choose because is fainted"])
            else:
                self.game.pop_state()
                self.add_monster_into_play(player, monster)

        state = self.game.push_state("MonsterMenuState")
        # must use a partial because alert relies on a text box that may not exist
        # until after the state hs been startup
        state.task(partial(state.alert, "Choose a replacement!"), 0)
        state.on_menu_selection = add

    def fill_battlefield_positions(self, ask=False):
        """ Check the battlefield for unfilled positions and send out monsters

        :param ask: bool.  if True, then open dialog for human players
        :return:
        """
        # TODO: let work for trainer battles
        humans = list(self.human_players)

        released = False
        for player in self.active_players:
            positions_available = self.max_positions - len(self.monsters_in_play[player])
            if positions_available:
                available = get_awake_monsters(player)
                for i in range(positions_available):
                    released = True
                    if player in humans and ask:
                        self.ask_player_for_monster(player)
                    else:
                        self.add_monster_into_play(player, next(available))

        if released:
            self.suppress_phase_change()

    def add_monster_into_play(self, player, monster):
        feet = list(self._layout[player]['home'][0].center)
        feet[1] += tools.scale(11)
        self.animate_monster_release_bottom(feet, monster)
        self.build_hud(self._layout[player]['hud'][0], monster)
        self.monsters_in_play[player].append(monster)

        # TODO: not hardcode
        if player is self.players[0]:
            self.alert('Go %s!' % monster.name.upper())
        else:
            self.alert('A wild %s appeared!' % monster.name.upper())

    def show_combat_dialog(self):
        """ Create and show the area where battle messages are displayed
        """
        # make the border and area at the bottom of the screen for messages
        x, y, w, h = self.game.screen.get_rect()
        rect = pygame.Rect(0, 0, w, h // 4)
        rect.bottomright = w, h
        border = tools.load_and_scale(self.borders_filename)
        self.dialog_box = GraphicBox(border, None, self.background_color)
        self.dialog_box.rect = rect
        self.sprites.add(self.dialog_box, layer=100)

        # make a text area to show messages
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.dialog_box.calc_inner_rect(self.dialog_box.rect)
        self.sprites.add(self.text_area, layer=100)

    def show_monster_action_menu(self, monster):
        """ Show the main window for choosing player actions

        :param monster: Monster to choose an action for
        :type monster: core.components.monster.Monster

        :returns: None
        """
        message = 'What will %s do?' % monster.name
        self.alert(message)
        x, y, w, h = self.game.screen.get_rect()
        rect = pygame.Rect(0, 0, w // 2.5, h // 4)
        rect.bottomright = w, h

        state = self.game.push_state("MainCombatMenuState", columns=2)
        state.monster = monster
        state.rect = rect

    def skip_phase_change(self):
        """ Skip phase change animations
        """
        for ani in self.animations:
            ani.finish()

    def enqueue_action(self, user, technique, target=None):
        self._action_queue.append(EnqueuedAction(user, technique, target))

    def remove_monster_actions_from_queue(self, monster):
        """ Remove all queued actions for a particular monster

        This is used mainly for removing actions after monster is fainted

        :type monster: core.components.monster.Monster
        :returns: None
        """
        to_remove = set()
        for action in self._action_queue:
            if action.user is monster or action.target is monster:
                to_remove.add(action)
        [self._action_queue.remove(action) for action in to_remove]

    def suppress_phase_change(self, delay=3):
        """ Prevent the combat phase from changing for a limited time

        Use this function to prevent the phase from changing.  When
        animating elements of the phase, call this to prevent player
        input as well as phase changes.

        :param delay:
        :return:
        """
        if self._animation_in_progress:
            logger.debug("double suppress: bug?")
        else:
            self._animation_in_progress = True
            self.task(partial(setattr, self, "_animation_in_progress", False), delay)

    def perform_action(self, user, technique, target=None):
        """ Do something with the thing: animated

        :param user:
        :param technique: Not a dict: a Technique or Item
        :param target:

        :returns:
        """
        result = technique.use(user, target)

        try:
            tools.load_sound(technique.sfx).play()
        except AttributeError:
            pass

        # action is performed, so now use sprites to animate it
        target_sprite = self._monster_sprite_map[target]

        hit_delay = 0
        if user:
            message = "%s used %s!" % (user.name, technique.name)

            # TODO: a real check or some params to test if should tackle, etc
            if technique in user.moves:
                hit_delay += .5
                user_sprite = self._monster_sprite_map[user]
                self.animate_sprite_tackle(user_sprite)
                self.task(partial(self.animate_sprite_take_damage, target_sprite), hit_delay + .2)
                self.task(partial(self.blink, target_sprite), hit_delay + .6)

            else:  # assume this was an item used
                if result:
                    message += "\nIt worked!"
                else:
                    message += "\nIt failed!"

            self.alert(message)
            self.suppress_phase_change()

        else:
            if result:
                self.suppress_phase_change()
                self.alert("{0.name} took {1.name} damage!".format(target, technique))

        if result and hasattr(technique, "images"):
            tech_sprite = self.get_technique_animation(technique)
            tech_sprite.rect.center = target_sprite.rect.center
            self.task(tech_sprite.image.play, hit_delay)
            self.task(partial(self.sprites.add, tech_sprite, layer=50), hit_delay)
            self.task(tech_sprite.kill, 3)

    def faint_monster(self, monster):
        """ Instantly make the monster faint (will be removed later)

        :type monster: core.components.monster.Monster
        :returns: None
        """
        monster.current_hp = 0
        monster.status = [faint]
        # TODO: award experience

    def animate_party_status(self):
        """ Animate monsters that need to be fainted

        * Animation to remove monster is handled here
        TODO: check for faint status, not HP

        :returns: None
        """
        for player in self.monsters_in_play.keys():
            for monster in self.monsters_in_play[player]:
                if fainted(monster):
                    self.alert("{0.name} fainted!".format(monster))
                    self.animate_monster_faint(monster)
                    self.suppress_phase_change(3)

    def check_party_hp(self):
        """ Apply status effects, then check HP, and party status

        * Monsters will be removed from play here

        :returns: None
        """
        for player in self.monsters_in_play.keys():
            for monster in self.monsters_in_play[player]:
                self.animate_hp(monster)
                if monster.current_hp <= 0:
                    self.remove_monster_actions_from_queue(monster)
                    self.faint_monster(monster)

    def get_technique_animation(self, technique):
        """ Return a sprite usable as a technique animation

        TODO: move to some generic animation loading thingy

        :type technique: core.components.monster.Technique
        :rtype: core.components.sprite.Sprite
        """
        try:
            return self._technique_cache[technique]
        except KeyError:
            sprite = self.load_technique_animation(technique)
            self._technique_cache[technique] = sprite
            return sprite

    @staticmethod
    def load_technique_animation(technique):
        """

        TODO: move to some generic animation loading thingy

        :param technique:
        :rtype: core.components.sprite.Sprite
        """
        frame_time = .09
        images = list()
        for fn in technique.images:
            image = tools.load_and_scale(fn)
            images.append((image, frame_time))

        tech = PygAnimation(images, False)
        sprite = Sprite()
        sprite.image = tech
        sprite.rect = tech.get_rect()
        return sprite

    @property
    def active_players(self):
        """ Generator of any non-defeated players/trainers

        :rtype: collections.Iterable[core.components.player.Player]
        """
        for player in self.players:
            if not defeated(player):
                yield player

    @property
    def human_players(self):
        # TODO: this.
        yield self.players[0]

    @property
    def ai_players(self):
        for player in set(self.active_players) - set(self.human_players):
            yield player

    @property
    def active_monsters(self):
        """ Generator of any non-defeated monsters on battlefield

        :rtype: collections.Iterable[core.components.monster.Monster]
        """
        for monsters in self.monsters_in_play.values():
            for monster in monsters:
                yield monster

    def remove_player(self, player):
        # TODO: non SP things
        self.players.remove(player)
        self.suppress_phase_change()
        self.alert("You have run away!")

    def check_match_status(self):
        """ Determine if match should continue or not

        :return:
        """
        if self._winner:
            return

        players = list(self.active_players)
        if len(players) == 1:
            self._winner = players[0]

            # TODO: proper match check, etc
            if self._winner.name == "Maple":
                self.alert("You've been defeated!")
            else:
                self.alert("You have won!")

    def end_combat(self):
        """ End the combat
        """
        # TODO: End combat differently depending on winning or losing

        # clear action queue
        self._action_queue = list()

        event_engine = self.game.event_engine
        fadeout_action = namedtuple("action", ["type", "parameters"])
        fadeout_action.type = "fadeout_music"
        fadeout_action.parameters = [1000]
        event_engine.actions["fadeout_music"]["method"](self.game, fadeout_action)

        # remove any menus that may be on top of the combat state
        while self.game.current_state is not self:
            self.game.pop_state()

        self.game.push_state("FadeOutTransition", caller=self)
