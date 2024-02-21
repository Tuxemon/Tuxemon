# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

General guidelines of the combat module
=======================================

- Animations and sprite changes should go in combat_animations.py
- Menus go in combat_menus.py
- This file should be uncoupled and to specific techniques and status

Actions where are dependant on specific techniques or actions should be
handled in an abstract way.  We should not be adding code, which for
example, is (pseudo code):

if monster.status == "confused":
    message("Monster is confused!")
    
Interactions like this should be handled in an abstract way.  If we keep
adding highly specific behaviours in this class, then it will be really
hard to modify and will conflict with the JSON files.

If you are faced with a situation where the best way is to add code like
this, then there is a lacking of structure that needs to be addressed.
In other words, it may be necessary to implement new functions to the
technique/status/combat classes that can do the needful without polluting
the class with hardcoded references to techniques/statuses.

There is already existing code like this, but it is not a validation to
add new code like it.  Consider it a priority to remove it when you are
able to. 

"""
from __future__ import annotations

import logging
import random
from collections.abc import Iterable, MutableMapping, Sequence
from functools import partial
from itertools import chain
from typing import Literal, NamedTuple, Optional, Union

import pygame
from pygame.rect import Rect

from tuxemon import audio, graphics, prepare, state, tools
from tuxemon.ai import AI
from tuxemon.animation import Animation, Task
from tuxemon.combat import (
    alive_party,
    award_experience,
    award_money,
    battlefield,
    check_moves,
    defeated,
    fainted,
    get_awake_monsters,
    get_winners,
    plague,
    set_var,
    track_battles,
)
from tuxemon.condition.condition import Condition
from tuxemon.db import BattleGraphicsModel, ItemCategory, PlagueType
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.states.monster import MonsterMenuState
from tuxemon.states.transition.fade import FadeOutTransition
from tuxemon.surfanim import SurfaceAnimation
from tuxemon.technique.technique import Technique
from tuxemon.tools import assert_never
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

from .combat_animations import CombatAnimations

logger = logging.getLogger(__name__)

CombatPhase = Literal[
    "begin",
    "ready",
    "housekeeping phase",
    "decision phase",
    "pre action phase",
    "action phase",
    "post action phase",
    "resolve match",
    "ran away",
    "draw match",
    "has winner",
    "end combat",
]


class EnqueuedAction(NamedTuple):
    user: Union[Monster, NPC, None]
    method: Union[Technique, Item, Condition, None]
    target: Monster


class DamageMap(NamedTuple):
    attack: Monster
    defense: Monster
    damage: int


def compute_text_animation_time(message: str) -> float:
    """
    Compute required time for a text animation.

    Parameters:
        message: The given text to be animated.

    Returns:
        The time in seconds expected to be taken by the animation.
    """
    return prepare.ACTION_TIME + prepare.LETTER_TIME * len(message)


class MethodAnimationCache:
    def __init__(self) -> None:
        self._sprites: dict[
            Union[Technique, Condition, Item], Optional[Sprite]
        ] = {}

    def get(
        self, method: Union[Technique, Condition, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return a sprite usable as a method (technique, item, condition) animation.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        try:
            return self._sprites[method]
        except KeyError:
            sprite = self.load_method_animation(method, is_flipped)
            self._sprites[method] = sprite
            return sprite

    @staticmethod
    def load_method_animation(
        method: Union[Technique, Condition, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return animated sprite from a technique, condition or item.

        Parameters:
            method: Whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the animation.

        """
        if not method.images:
            return None
        frame_time = 0.09
        images = list()
        for fn in method.images:
            image = graphics.load_and_scale(fn)
            images.append((image, frame_time))
        tech = SurfaceAnimation(images, False)
        if is_flipped:
            tech.flip(method.flip_axes)
        return Sprite(animation=tech)


class WaitForInputState(state.State):
    """Just wait for input blocking everything"""

    def process_event(self, event: PlayerInput) -> Optional[PlayerInput]:
        if event.pressed and event.button == buttons.A:
            self.client.pop_state(self)

        return None


class CombatState(CombatAnimations):
    """The state-menu responsible for all combat related tasks and functions.
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

    draw_borders = False
    escape_key_exits = False

    def __init__(
        self,
        players: tuple[NPC, NPC],
        graphics: BattleGraphicsModel,
        combat_type: Literal["monster", "trainer"],
    ) -> None:
        self.phase: Optional[CombatPhase] = None
        self._damage_map: list[DamageMap] = []
        self._method_cache = MethodAnimationCache()
        self._decision_queue: list[Monster] = []
        self._action_queue: list[EnqueuedAction] = []
        self._pending_queue: list[EnqueuedAction] = []
        self._log_action: list[tuple[int, EnqueuedAction]] = []
        self._monster_sprite_map: MutableMapping[Monster, Sprite] = {}
        self._layout = dict()  # player => home areas on screen
        self._turn: int = 0
        self._prize: int = 0
        self._captured_mon: Optional[Monster] = None
        self._new_tuxepedia: bool = False
        self._run: bool = False
        self._post_animation_task: Optional[Task] = None
        self._xp_message: Optional[str] = None
        self._random_tech_hit: float = 0.0

        super().__init__(players, graphics)
        self.is_trainer_battle = combat_type == "trainer"
        self.show_combat_dialog()
        self.transition_phase("begin")
        self.task(partial(setattr, self, "phase", "ready"), 3)

    @staticmethod
    def is_task_finished(task: Union[Task, Animation]) -> bool:
        """
        Check if the task is finished or not.
        In case the task is in fact an animation, it's considered as finished
        by default since it should not be blocking.

        Parameters:
            task: the task (or animation) to be checked

        Returns:
            False if the task is a task and not finished
        """
        if isinstance(task, Task):
            return task.is_finish()
        return True

    def update(self, time_delta: float) -> None:
        """
        Update the combat state.  State machine is checked.

        General operation:
        * determine what phase to update
        * if new phase, then run transition into new one
        * update the new phase, or the current one
        """
        super().update(time_delta)
        self._text_animation_time_left -= time_delta
        if self.no_ongoing_text_animation() and self.text_animations_queue:
            (
                next_animation,
                self._text_animation_time_left,
            ) = self.text_animations_queue.pop(0)
            next_animation()

        if self.no_ongoing_text_animation() and all(
            map(self.is_task_finished, self.animations)
        ):
            new_phase = self.determine_phase(self.phase)
            if new_phase:
                self.phase = new_phase
                self.transition_phase(new_phase)
            self.update_phase()

    def no_ongoing_text_animation(self) -> bool:
        """
        Return True if there is no current text animation.
        Return False otherwise.

        Returns:
            Whether there is no current text animation or not.
        """
        return self._text_animation_time_left <= 0

    def draw(self, surface: pygame.surface.Surface) -> None:
        """
        Draw combat state.

        Parameters:
            surface: Surface where to draw.

        """
        super().draw(surface)
        self.draw_hp_bars()
        self.draw_exp_bars()

    def draw_hp_bars(self) -> None:
        """Go through the HP bars and redraw them."""
        draw: bool = False
        for monster, hud in self.hud.items():
            rect = Rect(0, 0, tools.scale(70), tools.scale(8))
            rect.right = hud.image.get_width() - tools.scale(8)
            if hud.player and self.graphics.hud.hp_bar_player:
                rect.top += tools.scale(18)
                draw = True
            elif not hud.player and self.graphics.hud.hp_bar_opponent:
                rect.top += tools.scale(12)
                draw = True
            if draw:
                self._hp_bars[monster].draw(hud.image, rect)

    def draw_exp_bars(self) -> None:
        """Go through the EXP bars and redraw them."""
        for monster, hud in self.hud.items():
            if hud.player and self.graphics.hud.exp_bar_player:
                rect = Rect(0, 0, tools.scale(70), tools.scale(6))
                rect.right = hud.image.get_width() - tools.scale(8)
                rect.top += tools.scale(31)
                self._exp_bars[monster].draw(hud.image, rect)

    def determine_phase(
        self,
        phase: Optional[CombatPhase],
    ) -> Optional[CombatPhase]:
        """
        Determine the next phase and set it.

        Part of state machine
        Only test and set new phase.
        * Do not update phase actions
        * Try not to modify any values
        * Return a phase name and phase will change
        * Return None and phase will not change

        Parameters:
            phase: Current phase of the combat. Could be ``None`` if called
                before the combat had time to start.

        Returns:
            Next phase of the combat.

        """
        if phase is None or phase == "begin":
            return None

        elif phase == "ready":
            return "housekeeping phase"

        elif phase == "housekeeping phase":
            # this will wait for players to fill battleground positions
            for player in self.active_players:
                if len(alive_party(player)) == 1:
                    player.max_position = 1
                positions_available = player.max_position - len(
                    self.monsters_in_play[player]
                )
                if positions_available:
                    return None
            return "decision phase"

        elif phase == "decision phase":
            # TODO: only works for single player and if player runs
            if len(self.remaining_players) == 1:
                return "ran away"

            # assume each monster executes one action
            # if number of actions == monsters, then all monsters are ready
            elif len(self._action_queue) == len(self.active_monsters):
                return "pre action phase"

            return None

        elif phase == "pre action phase":
            return "action phase"

        elif phase == "action phase":
            if not self._action_queue:
                return "post action phase"

            return None

        elif phase == "post action phase":
            if not self._action_queue:
                return "resolve match"

            return None

        elif phase == "resolve match":
            remaining = len(self.remaining_players)

            if remaining == 0:
                return "draw match"
            elif remaining == 1:
                if self._run:
                    return "ran away"
                else:
                    return "has winner"
            else:
                return "housekeeping phase"

        elif phase == "ran away":
            return "end combat"

        elif phase == "draw match":
            return "end combat"

        elif phase == "has winner":
            return "end combat"

        elif phase == "end combat":
            return None

        else:
            assert_never(phase)

    def transition_phase(self, phase: CombatPhase) -> None:
        """
        Change from one phase from another.

        Part of state machine
        * Will be run just -once- when phase changes
        * Do not change phase
        * Execute code only to change into new phase
        * The phase's update will be executed -after- this

        Parameters:
            phase: Name of phase to transition to.

        """
        message = None
        if phase == "begin" or phase == "ready" or phase == "pre action phase":
            pass

        elif phase == "housekeeping phase":
            self._turn += 1
            # fill all battlefield positions, but on round 1, don't ask
            self.fill_battlefield_positions(ask=self._turn > 1)

            # plague
            # record the useful properties of the last monster we fought
            for player in self.remaining_players:
                if self.monsters_in_play[player]:
                    mon = self.monsters_in_play[player][0]
                    battlefield(local_session, mon, self.remaining_players)
                plague(player)

        elif phase == "decision phase":
            self.reset_status_icons()
            # saves random value, so we are able to reproduce
            # inside the condition files if a tech hit or missed
            value = random.random()
            self._random_tech_hit = value
            if not self._decision_queue:
                # tracks human players who need to choose an action
                for player in self.human_players:
                    self._decision_queue.extend(self.monsters_in_play[player])
                # tracks ai players who need to choose an action
                for trainer in self.ai_players:
                    for monster in self.monsters_in_play[trainer]:
                        AI(self, monster, trainer)
                        # recharge opponent moves
                        for tech in monster.moves:
                            tech.recharge()

        elif phase == "action phase":
            self.sort_action_queue()

        elif phase == "post action phase":
            # apply condition effects to the monsters
            for monster in self.active_monsters:
                # check if there are pending actions (eg. counterattacks)
                if self._pending_queue:
                    pend = None
                    for pending in self._pending_queue:
                        pend = pending
                    if pend:
                        self.enqueue_action(
                            pend.user, pend.method, pend.target
                        )
                        self._pending_queue.remove(pend)
                for condition in monster.status:
                    # validate condition
                    if condition.validate(monster):
                        condition.combat_state = self
                        # update counter nr turns
                        condition.nr_turn += 1
                        self.enqueue_action(None, condition, monster)
                    # avoid multiple effect condition
                    monster.set_stats()

        elif phase == "resolve match" or phase == "ran away":
            pass

        elif phase == "draw match":
            # it is a draw match; both players were defeated in same round
            draws = self.defeated_players
            for draw in draws:
                message = track_battles(
                    session=local_session,
                    output="draw",
                    player=draw,
                    players=draws,
                )

        elif phase == "has winner":
            winners = self.remaining_players
            losers = self.defeated_players
            message = ""
            for winner in winners:
                message = track_battles(
                    session=local_session,
                    output="won",
                    player=winner,
                    players=losers,
                    prize=self._prize,
                    trainer_battle=self.is_trainer_battle,
                )
            for loser in losers:
                message += "\n" + track_battles(
                    session=local_session,
                    output="lost",
                    player=loser,
                    players=winners,
                    trainer_battle=self.is_trainer_battle,
                )

        elif phase == "end combat":
            self.end_combat()

        else:
            assert_never(phase)

        if message:
            # push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            action_time = compute_text_animation_time(message)
            self.text_animations_queue.append(
                (partial(self.alert, message), action_time)
            )
            self.task(
                partial(self.client.push_state, WaitForInputState()),
                action_time,
            )

    def sort_action_queue(self) -> None:
        """Sort actions in the queue according to game rules.

        * Swap actions are always first
        * Techniques that damage are sorted by monster speed
        * Items are sorted by trainer speed

        """

        def rank_action(action: EnqueuedAction) -> tuple[int, int]:
            if action.method is None:
                return 0, 0
            sort = action.method.sort
            primary_order = prepare.SORT_ORDER.index(sort)

            if sort == "meta":
                # all meta items sorted together
                # use of 0 leads to undefined sort/probably random
                return primary_order, 0
            elif sort == "potion":
                return primary_order, 0
            else:
                # TODO: determine the secondary sort element,
                # monster speed, trainer speed, etc
                assert action.user
                return primary_order, action.user.speed_test(action)

        # TODO: Running happens somewhere else, it should be moved here
        # i think.
        # TODO: Eventually make an action queue class?
        self._action_queue.sort(key=rank_action, reverse=True)

    def update_phase(self) -> None:
        """
        Execute/update phase actions.

        Part of state machine
        * Do not change phase
        * Will be run each iteration phase is active
        * Do not test conditions to change phase

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

    def handle_action_queue(self) -> None:
        """Take one action from the queue and do it."""
        if self._action_queue:
            action = self._action_queue.pop()
            self.perform_action(*action)
            self.task(self.check_party_hp, 1)
            self.task(self.animate_party_status, 3)
            self.task(self.animate_xp_message, 3)

    def ask_player_for_monster(self, player: NPC) -> None:
        """
        Open dialog to allow player to choose a Tuxemon to enter into play.

        Parameters:
            player: Player who has to select a Tuxemon.

        """

        def add(menuitem: MenuItem[Monster]) -> None:
            monster = menuitem.game_object
            params = {"name": monster.name.upper()}
            if fainted(monster):
                dialog = T.format("combat_fainted", params)
                tools.open_dialog(local_session, [dialog])
            elif monster in self.active_monsters:
                dialog = T.format("combat_isactive", params)
                tools.open_dialog(local_session, [dialog])
            else:
                self.add_monster_into_play(player, monster)
                self.client.pop_state()

        state = self.client.push_state(MonsterMenuState())
        # must use a partial because alert relies on a text box that may not
        # exist until after the state hs been startup
        state.task(partial(state.alert, T.translate("combat_replacement")), 0)
        state.on_menu_selection = add  # type: ignore[assignment]
        state.escape_key_exits = False

    def fill_battlefield_positions(self, ask: bool = False) -> None:
        """
        Check the battlefield for unfilled positions and send out monsters.

        Parameters:
            ask: If True, then open dialog for human players.

        """
        # TODO: let work for trainer battles
        humans = list(self.human_players)

        # TODO: integrate some values for different match types
        for player in self.active_players:
            if len(alive_party(player)) == 1:
                player.max_position = 1
            positions_available = player.max_position - len(
                self.monsters_in_play[player]
            )
            if positions_available:
                available = get_awake_monsters(
                    player, self.monsters_in_play[player], self._turn
                )
                for _ in range(positions_available):
                    if player in humans and ask:
                        self.ask_player_for_monster(player)
                    else:
                        self.add_monster_into_play(player, next(available))

    def add_monster_into_play(
        self,
        player: NPC,
        monster: Monster,
        removed: Union[Monster, None] = None,
    ) -> None:
        """
        Add a monster to the battleground.

        Parameters:
            player: Player who adds the monster, if any.
            monster: Added monster.

        """
        item = Item()
        item.load(monster.capture_device)
        sprite = self._method_cache.get(item, False)
        assert sprite
        self.animate_monster_release(player, monster, sprite)
        self.monsters_in_play[player].append(monster)
        self.update_hud(player)

        # remove "bond" status (eg. lifeleech, etc.)
        for mon in self.active_monsters:
            if any(sta.bond for sta in monster.status):
                mon.status.clear()

        # TODO: not hardcode
        message = None
        if removed and removed.status:
            removed.status[0].combat_state = self
            removed.status[0].phase = "add_monster_into_play"
            removed.status[0].use(removed)

        params = {"target": monster.name.upper(), "user": player.name.upper()}
        if self._turn > 1:
            message = T.format("combat_swap", params)
        if message:
            self.text_animations_queue.append(
                (partial(self.alert, message), 0)
            )

    def reset_status_icons(self) -> None:
        """
        Update/reset status icons for monsters.

        TODO: caching, etc
        """
        # update huds
        for player in self.active_players:
            self.update_hud(player, False)
        # remove all status icons
        for s in self._status_icons.values():
            self.sprites.remove(s)
        self._status_icons.clear()

        # add status icons
        for monster in self.active_monsters:
            for status in monster.status:
                if status.icon:
                    status_ico: tuple[float, float] = (0.0, 0.0)
                    if len(self.monsters_in_play_left) > 1:
                        if monster == self.monsters_in_play_left[0]:
                            status_ico = prepare.ICON_OPPONENT_DEFAULT
                        elif monster == self.monsters_in_play_left[1]:
                            status_ico = prepare.ICON_OPPONENT_SLOT
                    else:
                        if monster == self.monsters_in_play_left[0]:
                            status_ico = prepare.ICON_OPPONENT_DEFAULT
                    if len(self.monsters_in_play_right) > 1:
                        if monster == self.monsters_in_play_right[0]:
                            status_ico = prepare.ICON_PLAYER_SLOT
                        elif monster == self.monsters_in_play_right[1]:
                            status_ico = prepare.ICON_PLAYER_DEFAULT
                    else:
                        if monster == self.monsters_in_play_right[0]:
                            status_ico = prepare.ICON_PLAYER_DEFAULT
                    # load the sprite and add it to the display
                    icon = self.load_sprite(
                        status.icon,
                        layer=200,
                        center=status_ico,
                    )
                    self._status_icons[monster].append(icon)

        # update tuxemon balls to reflect status
        self.animate_update_party_hud()

    def show_combat_dialog(self) -> None:
        """Create and show the area where battle messages are displayed."""
        # make the border and area at the bottom of the screen for messages
        rect_screen = self.client.screen.get_rect()
        rect = Rect(0, 0, rect_screen.w, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h
        border = graphics.load_and_scale(self.borders_filename)
        self.dialog_box = GraphicBox(border, None, self.background_color)
        self.dialog_box.rect = rect
        self.sprites.add(self.dialog_box, layer=100)

        # make a text area to show messages
        self.text_area = TextArea(self.font, self.font_color)
        self.text_area.rect = self.dialog_box.calc_inner_rect(
            self.dialog_box.rect,
        )
        self.sprites.add(self.text_area, layer=100)

    def show_monster_action_menu(self, monster: Monster) -> None:
        """
        Show the main window for choosing player actions.

        Parameters:
            monster: Monster to choose an action for.

        """
        name = "" if monster.owner is None else monster.owner.name
        params = {"name": monster.name, "player": name}
        message = T.format(self.graphics.msgid, params)
        self.text_animations_queue.append((partial(self.alert, message), 0))
        rect_screen = self.client.screen.get_rect()
        rect = Rect(0, 0, rect_screen.w // 2.5, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h

        state = self.client.push_state(
            self.graphics.menu, cmb=self, monster=monster
        )
        state.rect = rect

    def enqueue_damage(
        self, attacker: Monster, defender: Monster, damage: int
    ) -> None:
        """
        Add damages to damage map.

        Parameters:
            attacker: Monster.
            defender: Monster.
            damage: Quantity of damage.

        """
        damage_map = DamageMap(attacker, defender, damage)
        self._damage_map.append(damage_map)

    def enqueue_action(
        self,
        user: Union[NPC, Monster, None],
        technique: Union[Item, Technique, Condition, None],
        target: Monster,
    ) -> None:
        """
        Add some technique or status to the action queue.

        Parameters:
            user: The user of the technique.
            technique: The technique used.
            target: The target of the action.

        """
        action = EnqueuedAction(user, technique, target)
        self._action_queue.append(action)
        self._log_action.append((self._turn, action))

    def rewrite_action_queue_target(
        self, original: Monster, new: Monster
    ) -> None:
        """
        Used for swapping monsters.

        Parameters:
            original: Original targeted monster.
            new: New targeted monster.

        """
        # rewrite actions in the queue to target the new monster
        for index, action in enumerate(self._action_queue):
            if action.target is original:
                new_action = EnqueuedAction(action.user, action.method, new)
                self._action_queue[index] = new_action

    def rewrite_action_queue_method(
        self, attacker: Monster, method: Union[Technique, Item, Condition]
    ) -> None:
        """
        Used to replace the method (eg technique, item or condition) used.

        Parameters:
            attacker: Monster.
            technique: New technique used.

        eg. "monster uses RAM" -> "monster uses SABER"

        """
        # rewrite actions in the queue to target the new monster
        for index, action in enumerate(self._action_queue):
            if action.user == attacker:
                new_action = EnqueuedAction(action.user, method, action.target)
                self._action_queue[index] = new_action

    def remove_monster_from_play(
        self,
        monster: Monster,
    ) -> None:
        """
        Remove monster from play without fainting it.

        * If another monster has targeted this monster, it can change action
        * Will remove actions as well
        * currently for 'swap' technique

        """
        self.remove_monster_actions_from_queue(monster)
        self.animate_monster_faint(monster)

    def remove_monster_actions_from_queue(self, monster: Monster) -> None:
        """
        Remove all queued actions for a particular monster.

        This is used mainly for removing actions after monster is fainted.

        Parameters:
            monster: Monster whose actions will be removed.

        """
        to_remove = set()
        for action in self._action_queue:
            if action.user is monster or action.target is monster:
                to_remove.add(action)

        for action in to_remove:
            self._action_queue.remove(action)

    def perform_action(
        self,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, Condition, None],
        target: Monster,
    ) -> None:
        """
        Perform the action.

        Parameters:
            user: Monster that does the action.
            method: Technique or item or condition used.
            target: Monster that receives the action.

        """
        action_time = 0.0
        # action is performed, so now use sprites to animate it
        # this value will be None if the target is off screen
        target_sprite = self._monster_sprite_map.get(target, None)
        # slightly delay the monster shake, so technique animation
        # is synchronized with the damage shake motion
        hit_delay = 0.0
        # monster uses move
        if isinstance(method, Technique) and isinstance(user, Monster):
            method.advance_round()
            method.combat_state = self
            result_tech = method.use(user, target)
            context = {
                "user": user.name,
                "name": method.name,
                "target": target.name,
            }
            message: str = ""
            message += "\n" + T.format(method.use_tech, context)
            # swapping monster
            if method.slug == "swap":
                params = {"name": target.name.upper()}
                message = T.format("combat_call_tuxemon", params)
            # check statuses
            if user.status:
                user.status[0].combat_state = self
                user.status[0].phase = "perform_action_tech"
                result_status = user.status[0].use(user)
                if result_status["extra"]:
                    message += "\n" + result_status["extra"]
                if result_status["condition"]:
                    user.apply_status(result_status["condition"])
            # successful techniques
            if result_tech["success"]:
                m: Union[str, None] = None
                # extra output
                if result_tech["extra"]:
                    m = T.translate(result_tech["extra"])
                if m:
                    message += "\n" + m
                    action_time += compute_text_animation_time(message)
            # not successful techniques
            if not result_tech["success"]:
                template = getattr(method, "use_failure")
                m = T.format(template, context)
                # extra output
                if result_tech["extra"]:
                    m = T.translate(result_tech["extra"])
                message += "\n" + m
                action_time += compute_text_animation_time(message)
            # TODO: caching sounds
            audio.load_sound(method.sfx, None).play()
            # animation own monster, technique doesn't tackle
            hit_delay += 0.5
            if "own monster" in method.target:
                target_sprite = self._monster_sprite_map.get(user, None)
            # TODO: a real check or some params to test if should tackle, etc
            if result_tech["should_tackle"]:
                user_sprite = self._monster_sprite_map.get(user, None)
                if user_sprite:
                    self.animate_sprite_tackle(user_sprite)

                if target_sprite:
                    self.task(
                        partial(
                            self.animate_sprite_take_damage,
                            target_sprite,
                        ),
                        hit_delay + 0.2,
                    )
                    self.task(
                        partial(self.blink, target_sprite),
                        hit_delay + 0.6,
                    )

                # Track damage
                self.enqueue_damage(user, target, result_tech["damage"])

                # monster infected
                if user.plague == PlagueType.infected:
                    params = {"target": user.name.upper()}
                    m = T.format("combat_state_plague1", params)
                    message += "\n" + m
                # allows tackle to special range techniques too
                if method.range != "special":
                    element_damage_key = prepare.MULT_MAP.get(
                        result_tech["element_multiplier"]
                    )
                    if element_damage_key:
                        m = T.translate(element_damage_key)
                        message += "\n" + m
                        action_time += compute_text_animation_time(message)
                else:
                    msg_type = (
                        "use_success"
                        if result_tech["success"]
                        else "use_failure"
                    )
                    context = {
                        "user": getattr(user, "name", ""),
                        "name": method.name,
                        "target": target.name,
                    }
                    template = getattr(method, msg_type)
                    tmpl = T.format(template, context)
                    if template:
                        message += "\n" + tmpl
                        action_time += compute_text_animation_time(message)
            self.text_animations_queue.append(
                (partial(self.alert, message), action_time)
            )

            is_flipped = False
            for trainer in self.ai_players:
                if user in self.monsters_in_play[trainer]:
                    is_flipped = True
                    break
            tech_sprite = self._method_cache.get(method, is_flipped)

            if result_tech["success"] and target_sprite and tech_sprite:
                tech_sprite.rect.center = target_sprite.rect.center
                assert tech_sprite.animation
                self.task(tech_sprite.animation.play, hit_delay)
                self.task(
                    partial(self.sprites.add, tech_sprite, layer=50),
                    hit_delay,
                )
                self.task(tech_sprite.kill, action_time)

        # player uses item
        if isinstance(method, Item) and isinstance(user, NPC):
            method.combat_state = self
            result_item = method.use(user, target)
            context = {
                "user": user.name,
                "name": method.name,
                "target": target.name,
            }
            message = T.format(method.use_item, context)
            # animation sprite
            item_sprite = self._method_cache.get(method, False)
            # handle the capture device
            if method.category == ItemCategory.capture and item_sprite:
                # retrieve tuxeball
                message += "\n" + T.translate("attempting_capture")
                action_time = result_item["num_shakes"] + 1.8
                self.animate_capture_monster(
                    result_item["success"],
                    result_item["num_shakes"],
                    target,
                    method,
                    item_sprite,
                )
            else:
                msg_type = (
                    "use_success" if result_item["success"] else "use_failure"
                )
                context = {
                    "user": getattr(user, "name", ""),
                    "name": method.name,
                    "target": target.name,
                }
                template = getattr(method, msg_type)
                tmpl = T.format(template, context)
                # extra output
                if result_item["extra"]:
                    tmpl = T.translate(result_item["extra"])
                if template:
                    message += "\n" + tmpl
                    action_time += compute_text_animation_time(message)

                # item animation
                if target_sprite and item_sprite:
                    item_sprite.rect.center = target_sprite.rect.center
                    assert item_sprite.animation
                    self.task(item_sprite.animation.play, 0.6)
                    self.task(
                        partial(self.sprites.add, item_sprite, layer=50),
                        0.6,
                    )
                    self.task(item_sprite.kill, action_time)

            self.text_animations_queue.append(
                (partial(self.alert, message), action_time)
            )
        # statuses / conditions
        if isinstance(method, Condition):
            method.combat_state = self
            method.phase = "perform_action_status"
            method.advance_round()
            result = method.use(target)
            context = {
                "name": method.name,
                "target": target.name,
            }
            cond_mex: str = ""
            # successful conditions
            if result["success"]:
                if method.use_success:
                    template = getattr(method, "use_success")
                    cond_mex = T.format(template, context)
                # first turn status
                if method.nr_turn == 1 and method.gain_cond:
                    first_turn = getattr(method, "gain_cond")
                    first = T.format(first_turn, context)
                    cond_mex = first + "\n" + cond_mex
            # not successful conditions
            if not result["success"]:
                if method.use_failure:
                    template = getattr(method, "use_failure")
                    cond_mex = T.format(template, context)
            action_time += compute_text_animation_time(cond_mex)
            self.text_animations_queue.append(
                (partial(self.alert, cond_mex), action_time)
            )

            # effect animation
            is_flipped = False
            tech_sprite = self._method_cache.get(method, is_flipped)
            if target_sprite and tech_sprite:
                tech_sprite.rect.center = target_sprite.rect.center
                assert tech_sprite.animation
                self.task(tech_sprite.animation.play, 0.6)
                self.task(
                    partial(self.sprites.add, tech_sprite, layer=50),
                    0.6,
                )
                self.task(tech_sprite.kill, action_time)

    def faint_monster(self, monster: Monster) -> None:
        """
        Instantly make the monster faint (will be removed later).

        Parameters:
            monster: Monster that will faint.

        """
        monster.faint()
        iid = str(monster.instance_id.hex)
        label = f"{self.name.lower()}_faint"
        set_var(local_session, label, iid)

        """
        Experience is earned when the target monster is fainted.
        Any monsters who contributed any amount of damage will be awarded.
        Experience is distributed evenly to all participants.
        """
        message: str = ""
        action_time = 0.0

        winners = get_winners(monster, self._damage_map)
        if winners:
            for winner in winners:
                # Award money
                awarded_mon = award_money(monster, winner)
                # Award experience
                awarded_exp = award_experience(
                    monster, winner, self._damage_map
                )
                # check before giving exp
                levels = winner.give_experience(awarded_exp)
                # check after giving exp
                if self.is_trainer_battle:
                    self._prize += awarded_mon
                # it checks if there is a "level up"
                if winner in self.monsters_in_play_right:
                    # it checks if there is a "level up"
                    if levels >= 1:
                        mex = check_moves(winner, levels)
                        if mex:
                            message += "\n" + mex
                            action_time += compute_text_animation_time(message)
                        if winner.owner and winner.owner.isplayer:
                            del self.hud[winner]
                            self.update_hud(winner.owner, False)
                    params = {"name": winner.name.upper(), "xp": awarded_exp}
                    m = T.format("combat_gain_exp", params)
                    message += "\n" + m
            self._xp_message = message

            # Remove monster from damage map
            for element in self._damage_map:
                if element.defense == monster or element.attack == monster:
                    self._damage_map.remove(element)

    def animate_party_status(self) -> None:
        """
        Animate monsters that need to be fainted.

        * Animation to remove monster is handled here
        TODO: check for faint status, not HP

        """
        for _, party in self.monsters_in_play.items():
            for monster in party:
                if fainted(monster):
                    params = {"name": monster.name.upper()}
                    msg = T.format("combat_fainted", params)
                    self.text_animations_queue.append(
                        (partial(self.alert, msg), prepare.ACTION_TIME)
                    )
                    self.animate_monster_faint(monster)

    def animate_xp_message(self) -> None:
        if self._xp_message is not None:
            timed_text_animation = (
                partial(self.alert, self._xp_message),
                compute_text_animation_time(self._xp_message),
            )
            self.text_animations_queue.append(timed_text_animation)
            self._xp_message = None

    def check_party_hp(self) -> None:
        """
        Apply status effects, then check HP, and party status.

        * Monsters will be removed from play here

        """
        for _, party in self.monsters_in_play.items():
            for monster in party:
                self.animate_hp(monster)
                # check statuses
                if monster.status:
                    monster.status[0].combat_state = self
                    monster.status[0].phase = "check_party_hp"
                    result_status = monster.status[0].use(monster)
                    if result_status["extra"]:
                        extra = result_status["extra"]
                        action_time = compute_text_animation_time(extra)
                        self.text_animations_queue.append(
                            (partial(self.alert, extra), action_time)
                        )
                if fainted(monster):
                    self.remove_monster_actions_from_queue(monster)
                    self.faint_monster(monster)

                    # If a monster fainted, exp was given, thus the exp bar
                    # should be updated
                    # The exp bar must only be animated for the player's
                    # monsters
                    # Enemies don't have a bar, doing it for them will
                    # cause a crash
                    for monster in self.monsters_in_play_right:
                        self.task(partial(self.animate_exp, monster), 2.5)

    @property
    def active_players(self) -> Iterable[NPC]:
        """
        Generator of any non-defeated players/trainers.

        Returns:
            Iterable with active players.

        """
        for player in self.players:
            if not defeated(player):
                yield player

    @property
    def human_players(self) -> Iterable[NPC]:
        for player in self.players:
            if player.isplayer:
                yield player

    @property
    def ai_players(self) -> Iterable[NPC]:
        yield from set(self.active_players) - set(self.human_players)

    @property
    def active_monsters(self) -> Sequence[Monster]:
        """
        List of any non-defeated monsters on battlefield.

        Returns:
            Sequence of active monsters.

        """
        return list(chain.from_iterable(self.monsters_in_play.values()))

    @property
    def monsters_in_play_right(self) -> Sequence[Monster]:
        """
        List of any monsters in battle (right side).

        """
        return self.monsters_in_play[self.players[0]]

    @property
    def monsters_in_play_left(self) -> Sequence[Monster]:
        """
        List of any monsters in battle (left side).

        """
        return self.monsters_in_play[self.players[1]]

    @property
    def defeated_players(self) -> Sequence[NPC]:
        """
        List of defeated players/trainers.

        """
        return [p for p in self.players if defeated(p)]

    @property
    def remaining_players(self) -> Sequence[NPC]:
        """
        List of non-defeated players/trainers. WIP.

        Right now, this is similar to Combat.active_players, but it may change
        in the future.
        For implementing teams, this would need to be different than
        active_players.

        Use to check for match winner.

        Returns:
            Sequence of remaining players.

        """
        # TODO: perhaps change this to remaining "parties", or "teams",
        # instead of player/trainer
        return [p for p in self.players if not defeated(p)]

    def clean_combat(self) -> None:
        """Clean combat."""
        for player in self.players:
            player.max_position = 1
            for mon in player.monsters:
                # reset status stats
                mon.set_stats()
                mon.end_combat()
                # reset type
                mon.reset_types()
                # reset technique stats
                for tech in mon.moves:
                    tech.set_stats()

        # clear action queue
        self._action_queue = list()
        self._pending_queue = list()
        self._log_action = list()
        self._damage_map = list()

    def end_combat(self) -> None:
        """End the combat."""
        self.clean_combat()

        # fade music out
        self.client.event_engine.execute_action("fadeout_music", [1000])

        # remove any menus that may be on top of the combat state
        while self.client.current_state is not self:
            self.client.pop_state()

        self.phase = None
        # open Tuxepedia if monster is captured
        if self._captured_mon and self._new_tuxepedia:
            self.client.pop_state()
            params = {"monster": self._captured_mon, "source": self.name}
            self.client.push_state("MonsterInfoState", kwargs=params)
        else:
            self.client.push_state(FadeOutTransition(caller=self))
