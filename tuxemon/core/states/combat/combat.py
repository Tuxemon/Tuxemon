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
from collections import defaultdict, namedtuple
from functools import partial
from itertools import chain

import pygame

from core import state, tools
from core.components.locale import translator
from core.components.pyganim import PygAnimation
from core.components.sprite import Sprite
from core.components.technique import Technique
from core.components.ui.draw import GraphicBox
from core.components.ui.text import TextArea
from .combat_animations import CombatAnimations

trans = translator.translate

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("%s successfully imported" % __name__)

EnqueuedAction = namedtuple("EnqueuedAction", "user technique target")

faint = Technique("status_faint")


def check_status(monster, status_name):
    return any(t for t in monster.status if t.slug == status_name)


def fainted(monster):
    return check_status(monster, "status_faint")


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


class WaitForInputState(state.State):
    """ Just wait for input blocking everything
    """

    def process_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game.pop_state(self)


class CombatState(CombatAnimations):
    """ The state-menu responsible for all combat related tasks and functions.
        .. image:: images/combat/monster_drawing01.png

    General description of this class:
        * implements a simple state machine
        * various phases are executed using a queue of actions
        * "decision queue" is used to queue player interactions/menus
        * this class holds mostly logic, though some graphical functions exist
        * most graphical functions are contained in "CombatAnimations" class

    Currently, status icons are implemented as follows:
       each round, all status icons are destroyed
       status icons are created for each status on each monster
       obvs, not ideal, maybe someday make it better? (see transition_phase)
    """
    background_filename = "gfx/ui/combat/battle_bg03.png"
    draw_borders = False
    escape_key_exits = False

    def startup(self, **kwargs):
        self.max_positions = 1  # TODO: make dependant on match type
        self.phase = None
        self.monsters_in_play = defaultdict(list)
        self._damage_map = defaultdict(set)  # track damage so experience can be awarded later
        self._technique_cache = dict()  # cache for technique animations
        self._decision_queue = list()  # queue for monsters that need decisions
        self._position_queue = list()  # queue for asking players to add a monster into play (subject to change)
        self._action_queue = list()  # queue for techniques, items, and status effects
        self._status_icons = list()  # list of sprites that are status icons
        self._monster_sprite_map = dict()  # monster => sprite
        self._hp_bars = dict()  # monster => hp bar
        self._layout = dict()  # player => home areas on screen
        self._animation_in_progress = False  # if true, delay phase change
        self._round = 0

        super(CombatState, self).startup(**kwargs)
        self.players = list(self.players)
        self.show_combat_dialog()
        self.transition_phase("begin")
        self.task(partial(setattr, self, "phase", "ready"), 3)

    def update(self, time_delta):
        """ Update the combat state.  State machine is checked.

        General operation:
        * determine what phase to execute
        * if new phase, then run transition into new one
        * update the new phase, or the current one
        """
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

        Part of state machine
        Only test and set new phase.
        * Do not execute phase actions
        * Try not to modify any values
        * Return a phase name and phase will change
        * Return None and phase will not change

        :returns: None or String
        """
        if phase == "ready":
            return "housekeeping phase"

        elif phase == "housekeeping phase":
            # this will wait for players to fill battleground positions
            for player in self.active_players:
                positions_available = self.max_positions - len(self.monsters_in_play[player])
                if positions_available:
                    return

            # DO NOT REMOVE THIS CODE
            # enable it to test for draw matches
            if 0:
                t = Technique("technique_poison_sting")
                for p, m in self.monsters_in_play.items():
                    for m in m:
                        m.current_hp = min(m.current_hp, 1)
                        t.use(m, m)

            # enable to test for defeat in matches
            if 0:
                [setattr(m, 'current_hp', 1) for m in self.players[0].monsters]

            return "decision phase"

        elif phase == "decision phase":
            # TODO: only works for single player and if player runs
            if len(self.remaining_players) == 1:
                return "ran away"

            # assume each monster executes one action
            # if number of actions == monsters, then all monsters are ready
            if len(self._action_queue) == len(self.active_monsters):
                return "pre action phase"

        elif phase == "pre action phase":
            return "action phase"

        if phase == "action phase":
            if not self._action_queue:
                return "post action phase"

        elif phase == "post action phase":
            if not self._action_queue:
                return "resolve match"

        elif phase == "resolve match":
            remaining = len(self.remaining_players)

            if remaining == 0:
                return "draw match"
            elif remaining == 1:
                return "has winner"
            else:
                return "housekeeping phase"

        elif phase == "ran away":
            return "end combat"

        elif phase == "draw match":
            return "end combat"

        elif phase == "has winner":
            return "end combat"

    def transition_phase(self, phase):
        """ Change from one phase from another.

        Part of state machine
        * Will be run just -once- when phase changes.
        * Do not change phase.
        * Execute code only to change into new phase.
        * The phase's update will be executed -after- this

        :param phase:
        :return:
        """
        if phase == "housekeeping phase":
            self._round += 1
            # fill all battlefield positions, but on round 1, don't ask
            self.fill_battlefield_positions(ask=self._round > 1)

        if phase == "decision phase":
            self.reset_status_icons()
            if not self._decision_queue:
                for player in self.human_players:
                    # the decision queue tracks human players who need to choose an
                    # action
                    self._decision_queue.extend(self.monsters_in_play[player])

                for trainer in self.ai_players:
                    for monster in self.monsters_in_play[trainer]:
                        action = self.get_combat_decision_from_ai(monster)
                        self._action_queue.append(action)

        elif phase == "action phase":
            self.sort_action_queue()

        elif phase == "post action phase":
            # apply status effects to the monsters
            for monster in self.active_monsters:
                for technique in monster.status:
                    self.enqueue_action(None, technique, monster)

        elif phase == "resolve match":
            pass

        elif phase == "ran away":
            self.alert(trans('combat_player_run'))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            # if you run in PvP, you need "defeated message"
            self.task(partial(self.game.push_state, "WaitForInputState"), 2)
            self.suppress_phase_change(3)

        elif phase == "draw match":
            # it is a draw match; both players were defeated in same round
            self.alert(trans('combat_draw'))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            self.task(partial(self.game.push_state, "WaitForInputState"), 2)
            self.suppress_phase_change(3)

        elif phase == "has winner":
            # TODO: proper match check, etc
            # This assumes that player[0] is the human playing in single player
            if self.remaining_players[0] == self.players[0]:
                self.alert(trans('combat_victory'))
            else:
                self.alert(trans('combat_defeat'))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            self.task(partial(self.game.push_state, "WaitForInputState"), 2)
            self.suppress_phase_change(3)

        elif phase == "end combat":
            self.end_combat()

    def get_combat_decision_from_ai(self, monster):
        """ Get ai action from a monster and enqueue it
        
        :param monster: 
        :param opponents: 
        :return: 
        """
        # TODO: parties/teams/etc to choose opponents
        opponents = self.monsters_in_play[self.players[0]]
        technique, target = monster.ai.make_decision(monster, opponents)
        return EnqueuedAction(monster, technique, target)

    def sort_action_queue(self):
        """ Sort actions in the queue according to game rules
        
        * Swap actions are always first
        * Techniques that damage are sorted by monster speed
        * Items are sorted by trainer speed
        
        :return: 
        """

        def rank_action(action):
            sort = action.technique.sort
            primary_order = sort_order.index(sort)

            if sort == 'meta':
                # all meta items sorted together
                # use of 0 leads to undefined sort/probably random
                return primary_order, 0

            if sort == 'item':
                # should be trainer speed in this case
                return primary_order, action.user.speed

            if sort == 'damage':
                # should be monster speed in this case
                return primary_order, action.user.speed

            print('cannot sort action', action)
            raise RuntimeError

        sort_order = ['meta', 'item', 'heal', 'damage']

        # TODO: Running happens somewhere else, it should be moved here i think.
        # TODO: Eventually make an action queue class?
        self._action_queue.sort(key=rank_action, reverse=True)

    def update_phase(self):
        """ Execute/update phase actions

        Part of state machine
        * Do not change phase.
        * Will be run each iteration phase is active.
        * Do not test conditions to change phase.

        :return: None
        """
        if self.phase == "decision phase":
            # show monster action menu for human players
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
                tools.open_dialog(self.game, [trans("combat_fainted", parameters={"name": monster.name})])
            elif monster in self.active_monsters:
                tools.open_dialog(self.game, [trans("combat_isactive", parameters={"name": monster.name})])
                msg = trans("combat_replacement_is_fainted")
                tools.open_dialog(self.game, [msg])
            else:
                self.add_monster_into_play(player, monster)
                self.game.pop_state()

        state = self.game.push_state("MonsterMenuState")
        # must use a partial because alert relies on a text box that may not exist
        # until after the state hs been startup
        state.task(partial(state.alert, trans("combat_replacement")), 0)
        state.on_menu_selection = add

    def fill_battlefield_positions(self, ask=False):
        """ Check the battlefield for unfilled positions and send out monsters

        :param ask: bool.  if True, then open dialog for human players
        :return:
        """
        # TODO: let work for trainer battles
        humans = list(self.human_players)

        # TODO: integrate some values for different match types
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
        """

        :param player:
        :param monster:
        :return:
        """
        # TODO: refactor some into the combat animations
        feet = list(self._layout[player]['home'][0].center)
        feet[1] += tools.scale(11)
        self.animate_monster_release_bottom(feet, monster)
        self.build_hud(self._layout[player]['hud'][0], monster)
        self.monsters_in_play[player].append(monster)

        # TODO: not hardcode
        if player is self.players[0]:
            self.alert(trans('combat_call_tuxemon', {"name": monster.name.upper()}))
        else:
            self.alert(trans('combat_wild_appeared', {"name": monster.name.upper()}))

    def reset_status_icons(self):
        """ Update/reset status icons for monsters

        TODO: caching, etc
        """
        # remove all status icons
        for s in self._status_icons:
            self.sprites.remove(s)

        # add status icons
        for monster in self.active_monsters:
            for status in monster.status:
                if status.icon:
                    # get the rect of the monster
                    rect = self._monster_sprite_map[monster].rect
                    # load the sprite and add it to the display
                    self.load_sprite(status.icon, layer=200, center=rect.topleft)

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
        message = trans('combat_monster_choice', {"name": monster.name})
        self.alert(message)
        x, y, w, h = self.game.screen.get_rect()
        rect = pygame.Rect(0, 0, w // 2.5, h // 4)
        rect.bottomright = w, h

        state = self.game.push_state("MainCombatMenuState", columns=2)
        state.monster = monster
        state.rect = rect

    def skip_phase_change(self):
        """ Skip phase change animations

        Useful if player wants to skip a battle animation
        """
        for ani in self.animations:
            ani.finish()

    def enqueue_action(self, user, technique, target=None):
        """ Add some technique or status to the action queue

        :param user:
        :param technique:
        :param target:
        :returns: None
        """
        self._action_queue.append(EnqueuedAction(user, technique, target))

    def rewrite_action_queue_target(self, original, new):
        """ Used for swapping monsters
        
        :param original: 
        :param new: 
        :return: 
        """
        # rewrite actions in the queue to target the new monster
        for index, action in enumerate(self._action_queue):
            if action.target is original:
                new_action = EnqueuedAction(action.user, action.technique, new)
                self._action_queue[index] = new_action

    def remove_monster_from_play(self, trainer, monster):
        """ Remove monster from play without fainting it
        
        * If another monster has targeted this monster, it can change action
        * Will remove actions as well
        * currently for 'swap' technique
        
        :param monster: 
        :return: 
        """
        self.remove_monster_actions_from_queue(monster)
        self.animate_monster_faint(monster)

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

    def suppress_phase_change(self, delay=3.0):
        """ Prevent the combat phase from changing for a limited time

        Use this function to prevent the phase from changing.  When
        animating elements of the phase, call this to prevent player
        input as well as phase changes.

        :param delay:
        :return:
        """
        if self._animation_in_progress:
            logger.debug("double suppress: bug?")
            return

        self._animation_in_progress = True
        return self.task(partial(setattr, self, "_animation_in_progress", False), delay)

    def perform_action(self, user, technique, target=None):
        """ Do something with the thing: animated

        :param user:
        :param technique: Not a dict: a Technique or Item
        :param target:

        :returns:
        """
        technique.advance_round()

        # This is the time, in seconds, that the animation takes to finish.
        action_time = 3.0
        result = technique.use(user, target)

        if technique.execute_trans:
            context = {"user": getattr(user, "name", ''),
                       "name": technique.name,
                       "target": target.name}
            message = trans(technique.execute_trans, context)
        else:
            message = ''

        try:
            tools.load_sound(technique.sfx).play()
        except AttributeError:
            pass

        # action is performed, so now use sprites to animate it
        # this value will be None if the target is off screen
        target_sprite = self._monster_sprite_map.get(target, None)

        # slightly delay the monster shake, so technique animation
        # is synchronized with the damage shake motion
        hit_delay = 0
        if user:

            # TODO: a real check or some params to test if should tackle, etc
            if result["should_tackle"]:
                hit_delay += .5
                user_sprite = self._monster_sprite_map[user]
                self.animate_sprite_tackle(user_sprite)

                if target_sprite:
                    self.task(partial(self.animate_sprite_take_damage, target_sprite), hit_delay + .2)
                    self.task(partial(self.blink, target_sprite), hit_delay + .6)

                # TODO: track total damage
                # Track damage
                self._damage_map[target].add(user)

            else:  # assume this was an item used

                # handle the capture device
                if result["capture"]:
                    message += "\n" + trans('attempting_capture')
                    action_time = result["num_shakes"] + 1.8
                    self.animate_capture_monster(result["success"], result["num_shakes"], target)

                    # TODO: Don't end combat right away; only works with SP, and 1 member parties
                    # end combat right here
                    if result["success"]:
                        self.task(self.end_combat, action_time + 0.5)  # Display 'Gotcha!' first.
                        self.task(partial(self.alert, trans('gotcha')), action_time)
                        self._animation_in_progress = True
                        return

                # generic handling of anything else
                else:
                    msg_type = 'success_trans' if result['success'] else 'failure_trans'
                    template = getattr(technique, msg_type)
                    if template:
                        message += "\n" + trans(template)

            self.alert(message)
            self.suppress_phase_change(action_time)

        else:
            if result["success"]:
                self.suppress_phase_change()
                self.alert(trans('combat_status_damage', {"name": target.name, "status": technique.name}))

        if result["success"] and target_sprite and hasattr(technique, "images"):
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

        """
        Experience is earned when the target monster is fainted.
        Any monsters who contributed any amount of damage will be awarded
        Experience is distributed evenly to all participants
        """
        if monster in self._damage_map:
            # Award Experience
            awarded_exp = monster.total_experience / monster.level / len(self._damage_map[monster])
            for winners in self._damage_map[monster]:
                winners.give_experience(awarded_exp)

            # Remove monster from damage map
            del self._damage_map[monster]

    def animate_party_status(self):
        """ Animate monsters that need to be fainted

        * Animation to remove monster is handled here
        TODO: check for faint status, not HP

        :returns: None
        """
        for player, party in self.monsters_in_play.items():
            for monster in party:
                if fainted(monster):
                    self.alert(trans('combat_fainted', {"name": monster.name}))
                    self.animate_monster_faint(monster)
                    self.suppress_phase_change(3)

    def check_party_hp(self):
        """ Apply status effects, then check HP, and party status

        * Monsters will be removed from play here

        :returns: None
        """
        for player, party in self.monsters_in_play.items():
            for monster in party:
                self.animate_hp(monster)
                if monster.current_hp <= 0 and not fainted(monster):
                    self.remove_monster_actions_from_queue(monster)
                    self.faint_monster(monster)

    def get_technique_animation(self, technique):
        """ Return a sprite usable as a technique animation

        TODO: move to some generic animation loading thingy

        :type technique: core.components.technique.Technique
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
        for player in self.players:
            if player.isplayer:
                yield player

    @property
    def ai_players(self):
        for player in set(self.active_players) - set(self.human_players):
            yield player

    @property
    def active_monsters(self):
        """ List of any non-defeated monsters on battlefield

        :rtype: list
        """
        return list(chain.from_iterable(self.monsters_in_play.values()))

    @property
    def remaining_players(self):
        """ List of non-defeated players/trainers.  WIP

        right now, this is similar to Combat.active_players, but it may change in the future.
        For implementing teams, this would need to be different than active_players

        Use to check for match winner

        :return: list
        """
        # TODO: perhaps change this to remaining "parties", or "teams", instead of player/trainer
        return [p for p in self.players if not defeated(p)]

    def trigger_player_run(self, player):
        """ WIP.  make player run from battle

        This is a temporary fix for now.  Expected to be called by the command menu.

        :param player: 
        :return: 
        """
        # TODO: non SP things
        del self.monsters_in_play[player]
        self.players.remove(player)

    def end_combat(self):
        """ End the combat
        """
        # TODO: End combat differently depending on winning or losing

        # clear action queue
        self._action_queue = list()

        contexts = {}
        event_engine = self.game.event_engine
        fadeout_action = namedtuple("action", ["type", "parameters"])
        fadeout_action.type = "fadeout_music"
        fadeout_action.parameters = [1000]
        event_engine.actions["fadeout_music"]["method"](self.game, fadeout_action, contexts)
        for key in contexts:
            contexts[key].execute(game)

        # remove any menus that may be on top of the combat state
        while self.game.current_state is not self:
            self.game.pop_state()

        self.game.push_state("FadeOutTransition", caller=self)
