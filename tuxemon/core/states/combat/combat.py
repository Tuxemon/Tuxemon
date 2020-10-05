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

import logging
from collections import defaultdict, namedtuple
from functools import partial
from itertools import chain

from tuxemon.compat import Rect
from tuxemon.core import audio, state, tools, graphics
from tuxemon.core.combat import check_status, fainted, get_awake_monsters, defeated
from tuxemon.core.locale import T
from tuxemon.core.platform.const import buttons
from tuxemon.core.pyganim import PygAnimation
from tuxemon.core.session import local_session
from tuxemon.core.sprite import Sprite
from tuxemon.core.technique import Technique
from tuxemon.core.ui.draw import GraphicBox
from tuxemon.core.ui.text import TextArea
from .combat_animations import CombatAnimations

logger = logging.getLogger(__name__)

EnqueuedAction = namedtuple("EnqueuedAction", "user technique target")

faint = Technique("status_faint")

# TODO: move to mod config
MULT_MAP = {
    4: "attack_very_effective",
    2: "attack_effective",
    0.5: "attack_resisted",
    0.25: "attack_weak",
}


class TechniqueAnimationCache:
    def __init__(self):
        self._sprites = dict()

    def get(self, technique):
        """ Return a sprite usable as a technique animation

        :type technique: tuxemon.core.technique.Technique
        :rtype: tuxemon.core.sprite.Sprite
        """
        try:
            return self._sprites[technique]
        except KeyError:
            sprite = self.load_technique_animation(technique)
            self._sprites[technique] = sprite
            return sprite

    @staticmethod
    def load_technique_animation(technique):
        """ Return animated sprite from a technique

        :param tuxemon.core.technique.Technique technique:
        :rtype: tuxemon.core.sprite.Sprite
        """
        if not technique.images:
            return None
        frame_time = .09
        images = list()
        for fn in technique.images:
            image = graphics.load_and_scale(fn)
            images.append((image, frame_time))
        tech = PygAnimation(images, False)
        sprite = Sprite()
        sprite.image = tech
        sprite.rect = tech.get_rect()
        return sprite


class WaitForInputState(state.State):
    """ Just wait for input blocking everything
    """

    def process_event(self, event):
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: tuxemon.core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
        """
        if event.pressed and event.button == buttons.A:
            self.client.pop_state(self)


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
        self._technique_cache = TechniqueAnimationCache()
        self._decision_queue = list()  # queue for monsters that need decisions
        self._position_queue = list()  # queue for asking players to add a monster into play (subject to change)
        self._action_queue = list()  # queue for techniques, items, and status effects
        self._status_icons = list()  # list of sprites that are status icons
        self._monster_sprite_map = dict()  # monster => sprite
        self._hp_bars = dict()  # monster => hp bar
        self._exp_bars = dict()  # monster => exp bar
        self._layout = dict()  # player => home areas on screen
        self._animation_in_progress = False  # if true, delay phase change
        self._round = 0

        super().startup(**kwargs)
        self.is_trainer_battle = kwargs.get('combat_type') == "trainer"
        self.players = list(self.players)
        self.graphics = kwargs.get('graphics')
        self.show_combat_dialog()
        self.transition_phase("begin")
        self.task(partial(setattr, self, "phase", "ready"), 3)

    def update(self, time_delta):
        """ Update the combat state.  State machine is checked.

        General operation:
        * determine what phase to update
        * if new phase, then run transition into new one
        * update the new phase, or the current one
        """
        super().update(time_delta)
        if not self._animation_in_progress:
            new_phase = self.determine_phase(self.phase)
            if new_phase:
                self.phase = new_phase
                self.transition_phase(new_phase)
            self.update_phase()

    def draw(self, surface):
        """ Draw combat state

        :param pygame.surface.Surface surface:
        :rtype: None
        """
        super().draw(surface)
        self.draw_hp_bars()
        self.draw_exp_bars()

    def draw_hp_bars(self):
        """ Go through the HP bars and redraw them

        :rtype: None
        """
        for monster, hud in self.hud.items():
            rect = Rect(0, 0, tools.scale(70), tools.scale(8))
            rect.right = hud.image.get_width() - tools.scale(8)
            rect.top += tools.scale(12)
            self._hp_bars[monster].draw(hud.image, rect)

    def draw_exp_bars(self):
        """ Go through the EXP bars and redraw them

        :rtype: None
        """
        for monster, hud in self.hud.items():
            if hud.player:
                rect = Rect(0, 0, tools.scale(70), tools.scale(6))
                rect.right = hud.image.get_width() - tools.scale(8)
                rect.top += tools.scale(31)
                self._exp_bars[monster].draw(hud.image, rect)

    def determine_phase(self, phase):
        """ Determine the next phase and set it

        Part of state machine
        Only test and set new phase.
        * Do not update phase actions
        * Try not to modify any values
        * Return a phase name and phase will change
        * Return None and phase will not change

        :rtype: None or String
        """
        if phase == "ready":
            return "housekeeping phase"

        elif phase == "housekeeping phase":
            # this will wait for players to fill battleground positions
            for player in self.active_players:
                positions_available = self.max_positions - len(self.monsters_in_play[player])
                if positions_available:
                    return
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
        * Will be run just -once- when phase changes
        * Do not change phase
        * Execute code only to change into new phase
        * The phase's update will be executed -after- this

        :param str phase: Name of phase to transition to
        :rtype: None
        """
        if phase == "housekeeping phase":
            self._round += 1
            # fill all battlefield positions, but on round 1, don't ask
            self.fill_battlefield_positions(ask=self._round > 1)

            # record the useful properties of the last monster we fought
            monster_record = self.monsters_in_play[self.players[1]][0]
            if monster_record in self.active_monsters:
                self.players[0].game_variables['battle_last_monster_name'] = monster_record.name
                self.players[0].game_variables['battle_last_monster_level'] = monster_record.level
                self.players[0].game_variables['battle_last_monster_type'] = monster_record.slug
                self.players[0].game_variables['battle_last_monster_category'] = monster_record.category
                self.players[0].game_variables['battle_last_monster_shape'] = monster_record.shape

        if phase == "decision phase":
            self.reset_status_icons()
            if not self._decision_queue:
                for player in self.human_players:
                    # tracks human players who need to choose an action
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
            self.players[0].set_party_status()
            self.players[0].game_variables['battle_last_result'] = 'ran'
            self.alert(T.translate('combat_player_run'))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            # if you run in PvP, you need "defeated message"
            self.task(partial(self.client.push_state, "WaitForInputState"), 2)
            self.suppress_phase_change(3)

        elif phase == "draw match":
            self.players[0].set_party_status()
            self.players[0].game_variables['battle_last_result'] = 'draw'

            # it is a draw match; both players were defeated in same round
            self.alert(T.translate('combat_draw'))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            self.task(partial(self.client.push_state, "WaitForInputState"), 2)
            self.suppress_phase_change(3)

        elif phase == "has winner":
            # TODO: proper match check, etc
            # This assumes that player[0] is the human playing in single player
            self.players[0].set_party_status()
            if self.remaining_players[0] == self.players[0]:
                self.players[0].game_variables['battle_last_result'] = 'won'
                self.alert(T.translate('combat_victory'))
            else:
                self.players[0].game_variables['battle_last_result'] = 'lost'
                self.players[0].game_variables['battle_lost_faint'] = 'true'
                self.alert(T.translate('combat_defeat'))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            self.task(partial(self.client.push_state, "WaitForInputState"), 2)
            self.suppress_phase_change(3)

        elif phase == "end combat":
            self.players[0].set_party_status()
            self.end_combat()

    def get_combat_decision_from_ai(self, monster):
        """ Get ai action from a monster and enqueue it

        :param monster:
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

            else:
                # TODO: determine the secondary sort element, monster speed, trainer speed, etc
                return primary_order, action.user.speed_test(action)

        # TODO: move to mod config
        sort_order = ['meta', 'item', 'utility', 'potion', 'food', 'heal', 'damage']

        # TODO: Running happens somewhere else, it should be moved here i think.
        # TODO: Eventually make an action queue class?
        self._action_queue.sort(key=rank_action, reverse=True)

    def update_phase(self):
        """ Execute/update phase actions

        Part of state machine
        * Do not change phase
        * Will be run each iteration phase is active
        * Do not test conditions to change phase

        :rtype: None
        """
        if self.phase == "decision phase":
            # show monster action menu for human players
            if self._decision_queue:
                monster = self._decision_queue.pop()
                for tech in monster.moves:
                    tech.recharge()
                self.show_monster_action_menu(monster)

        elif self.phase == "action phase":
            self.handle_action_queue()

        elif self.phase == "post action phase":
            self.handle_action_queue()

    def handle_action_queue(self):
        """ Take one action from the queue and do it

        :rtype: None
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
                tools.open_dialog(local_session, [T.format("combat_fainted", parameters={"name": monster.name})])
            elif monster in self.active_monsters:
                tools.open_dialog(local_session, [T.format("combat_isactive", parameters={"name": monster.name})])
                msg = T.translate("combat_replacement_is_fainted")
                tools.open_dialog(local_session, [msg])
            else:
                self.add_monster_into_play(player, monster)
                self.client.pop_state()

        state = self.client.push_state("MonsterMenuState")
        # must use a partial because alert relies on a text box that may not exist
        # until after the state hs been startup
        state.task(partial(state.alert, T.translate("combat_replacement")), 0)
        state.on_menu_selection = add
        state.escape_key_exits = False

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
        self.animate_monster_release(player, monster)
        self.build_hud(self._layout[player]['hud'][0], monster)
        self.monsters_in_play[player].append(monster)

        # TODO: not hardcode
        if player is self.players[0]:
            self.alert(T.format('combat_call_tuxemon', {"name": monster.name.upper()}))
        elif self.is_trainer_battle:
            self.alert(
                T.format('combat_opponent_call_tuxemon', {
                    "name": monster.name.upper(),
                    "user": player.name.upper(),
                })
            )
        else:
            self.alert(T.format('combat_wild_appeared', {"name": monster.name.upper()}))

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
        x, y, w, h = self.client.screen.get_rect()
        rect = Rect(0, 0, w, h // 4)
        rect.bottomright = w, h
        border = graphics.load_and_scale(self.borders_filename)
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
        :type monster: tuxemon.core.monster.Monster

        :rtype: None
        """
        message = T.format('combat_monster_choice', {"name": monster.name})
        self.alert(message)
        x, y, w, h = self.client.screen.get_rect()
        rect = Rect(0, 0, w // 2.5, h // 4)
        rect.bottomright = w, h

        state = self.client.push_state("MainCombatMenuState", columns=2)
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

        :param tuxemon.core.npc.NPC user:
        :param tuxemon.core.technique.Technique technique:
        :param Optional[Union[NPC, Monster] target:
        :rtype: None
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

        :param tuxemon.core.monster.Monster monster:
        :rtype: None
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
        :param Union[Technique, Item] technique:
        :param target:

        :rtype: None
        """
        technique.advance_round()

        # This is the time, in seconds, that the animation takes to finish.
        action_time = 3.0
        result = technique.use(user, target)

        if technique.use_item:
            # "Monster used move!"
            context = {"user": getattr(user, "name", ''),
                       "name": technique.name,
                       "target": target.name}
            message = T.format(technique.use_item, context)
        else:
            message = ''

        # TODO: caching sounds
        audio.load_sound(technique.sfx).play()

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

                element_damage_key = MULT_MAP.get(result['element_multiplier'])
                if element_damage_key:
                    m = T.translate(element_damage_key)
                    message += "\n" + m

                for status in result.get("statuses", []):
                    m = T.format(status.use_item,
                                 {"name": technique.name, "user": status.link.name if status.link else "", "target": status.carrier.name})
                    message += "\n" + m

            else:  # assume this was an item used

                # handle the capture device
                if result["capture"]:
                    message += "\n" + T.translate('attempting_capture')
                    action_time = result["num_shakes"] + 1.8
                    self.animate_capture_monster(result["success"], result["num_shakes"], target)

                    # TODO: Don't end combat right away; only works with SP, and 1 member parties
                    # end combat right here
                    if result["success"]:
                        self.task(self.end_combat, action_time + 0.5)  # Display 'Gotcha!' first.
                        self.task(partial(self.alert, T.translate('gotcha')), action_time)
                        self._animation_in_progress = True
                        return

                # generic handling of anything else
                else:
                    msg_type = 'use_success' if result['success'] else 'use_failure'
                    template = getattr(technique, msg_type)
                    if template:
                        message += "\n" + T.translate(template)

            self.alert(message)
            self.suppress_phase_change(action_time)

        else:
            if result["success"]:
                self.suppress_phase_change()
                self.alert(T.format('combat_status_damage', {"name": target.name, "status": technique.name}))

        tech_sprite = self._technique_cache.get(technique)
        if result["success"] and target_sprite and tech_sprite:
            tech_sprite.rect.center = target_sprite.rect.center
            self.task(tech_sprite.image.play, hit_delay)
            self.task(partial(self.sprites.add, tech_sprite, layer=50), hit_delay)
            self.task(tech_sprite.kill, 3)

    def faint_monster(self, monster):
        """ Instantly make the monster faint (will be removed later)

        :type monster: tuxemon.core.monster.Monster
        :rtype: None
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

        :rtype: None
        """
        for player, party in self.monsters_in_play.items():
            for monster in party:
                if fainted(monster):
                    self.alert(T.format('combat_fainted', {"name": monster.name}))
                    self.animate_monster_faint(monster)
                    self.suppress_phase_change(3)

    def check_party_hp(self):
        """ Apply status effects, then check HP, and party status

        * Monsters will be removed from play here

        :rtype: None
        """
        for player, party in self.monsters_in_play.items():
            for monster in party:
                self.animate_hp(monster)
                if monster.current_hp <= 0 and not check_status(monster, "status_faint"):
                    self.remove_monster_actions_from_queue(monster)
                    self.faint_monster(monster)

                    # If a monster fainted, exp was given, thus the exp bar should be updated
                    # The exp bar must only be animated for the player's monsters
                    # Enemies don't have a bar, doing it for them will cause a crash
                    for monster in self.monsters_in_play[local_session.player]:
                        self.animate_exp(monster)

    @property
    def active_players(self):
        """ Generator of any non-defeated players/trainers

        :rtype: collections.Iterable[core.player.Player]
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
        yield from set(self.active_players) - set(self.human_players)

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
        for player in self.active_players:
            for mon in player.monsters:
                mon.end_combat()

        # clear action queue
        self._action_queue = list()

        # fade music out
        self.client.event_engine.execute_action("fadeout_music", [1000])

        # remove any menus that may be on top of the combat state
        while self.client.current_state is not self:
            self.client.pop_state()

        self.client.push_state("FadeOutTransition", caller=self)
