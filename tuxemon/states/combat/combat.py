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
from typing import Literal, Optional, Union

import pygame
from pygame.rect import Rect

from tuxemon import graphics, prepare, state, tools
from tuxemon.ai import AI
from tuxemon.animation import Animation, Task
from tuxemon.combat import (
    alive_party,
    award_experience,
    award_money,
    battlefield,
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
from tuxemon.technique.technique import Technique
from tuxemon.tools import assert_never
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

from .combat_animations import CombatAnimations
from .combat_classes import (
    ActionQueue,
    DamageReport,
    EnqueuedAction,
    MethodAnimationCache,
)

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


def compute_text_animation_time(message: str) -> float:
    """
    Compute required time for a text animation.

    Parameters:
        message: The given text to be animated.

    Returns:
        The time in seconds expected to be taken by the animation.
    """
    return prepare.ACTION_TIME + prepare.LETTER_TIME * len(message)


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
        self._damage_map: list[DamageReport] = []
        self._method_cache = MethodAnimationCache()
        self._action_queue = ActionQueue()
        self._decision_queue: list[Monster] = []
        self._pending_queue: list[EnqueuedAction] = []
        self._monster_sprite_map: MutableMapping[Monster, Sprite] = {}
        self._layout = dict()  # player => home areas on screen
        self._turn: int = 0
        self._prize: int = 0
        self._captured_mon: Optional[Monster] = None
        self._new_tuxepedia: bool = False
        self._run: bool = False
        self._post_animation_task: Optional[Task] = None
        self._xp_message: Optional[str] = None
        self._status_icon_cache: dict[
            tuple[str, tuple[float, float]], Sprite
        ] = {}
        self._random_tech_hit: dict[Monster, float] = {}

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

    def create_rect_for_bar(
        self, hud: Sprite, width: int, height: int, top_offset: int = 0
    ) -> Rect:
        """
        Creates a Rect object for a bar.

        Parameters:
            hud: The HUD sprite.
            width: The width of the bar.
            height: The height of the bar.
            top_offset: The top offset of the bar.

        Returns:
            A Rect object representing the bar.
        """
        rect = Rect(0, 0, tools.scale(width), tools.scale(height))
        rect.right = hud.image.get_width() - tools.scale(8)
        rect.top += tools.scale(top_offset)
        return rect

    def draw_hp_bars(self) -> None:
        """Go through the HP bars and redraw them."""
        show_player_hp = self.graphics.hud.hp_bar_player
        show_opponent_hp = self.graphics.hud.hp_bar_opponent

        for monster, hud in self.hud.items():
            if hud.player and show_player_hp:
                rect = self.create_rect_for_bar(hud, 70, 8, 18)
            elif not hud.player and show_opponent_hp:
                rect = self.create_rect_for_bar(hud, 70, 8, 12)
            else:
                continue
            self._hp_bars[monster].draw(hud.image, rect)

    def draw_exp_bars(self) -> None:
        """Go through the EXP bars and redraw them."""
        show_player_exp = self.graphics.hud.exp_bar_player

        for monster, hud in self.hud.items():
            if hud.player and show_player_exp:
                rect = self.create_rect_for_bar(hud, 70, 6, 31)
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
            elif len(self._action_queue.queue) == len(self.active_monsters):
                return "pre action phase"

            return None

        elif phase == "pre action phase":
            return "action phase"

        elif phase == "action phase":
            if self._action_queue.is_empty():
                return "post action phase"

            return None

        elif phase == "post action phase":
            if self._action_queue.is_empty():
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
            if not self._decision_queue:
                for player in list(self.human_players) + list(self.ai_players):
                    for monster in self.monsters_in_play[player]:
                        value = random.random()
                        self._random_tech_hit[monster] = value
                        if player in self.human_players:
                            self._decision_queue.append(monster)
                        else:
                            for tech in monster.moves:
                                tech.recharge()
                            AI(self, monster, player)

        elif phase == "action phase":
            self._action_queue.sort()

        elif phase == "post action phase":
            # remove actions from fainted users from the pending queue
            self._pending_queue = [
                pend
                for pend in self._pending_queue
                if pend.user
                and isinstance(pend.user, Monster)
                and not (fainted(pend.user) or fainted(pend.target))
            ]

            # apply condition effects to the monsters
            for monster in self.active_monsters:
                # Check if there are pending actions (e.g. counterattacks)
                while self._pending_queue:
                    pend = self._pending_queue.pop(0)
                    self.enqueue_action(pend.user, pend.method, pend.target)

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
        if not self._action_queue.is_empty():
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
        removed: Optional[Monster] = None,
    ) -> None:
        """
        Add a monster to the battleground.

        Parameters:
            player: Player who adds the monster, if any.
            monster: Added monster.
            removed: Monster that was previously in play, if any.

        """
        capture_device = Item()
        capture_device.load(monster.capture_device)
        sprite = self._method_cache.get(capture_device, False)
        if not sprite:
            raise ValueError(f"Sprite not found for item {capture_device}")

        self.monsters_in_play[player].append(monster)
        self.animate_monster_release(player, monster, sprite)
        self.update_hud(player)

        # Remove "bond" status from all active monsters
        for mon in self.active_monsters:
            mon.status = [sta for sta in mon.status if not sta.bond]

        # Handle removed monster's status effects
        if removed is not None and removed.status:
            removed.status[0].combat_state = self
            removed.status[0].phase = "add_monster_into_play"
            removed.status[0].use(removed)

        # Create message for combat swap
        format_params = {
            "target": monster.name.upper(),
            "user": player.name.upper(),
        }
        if self._turn > 1:
            message = T.format("combat_swap", format_params)
            self.text_animations_queue.append(
                (partial(self.alert, message), 0)
            )

    def get_status_icon_position(
        self, monster: Monster, monsters_in_play: Sequence[Monster]
    ) -> tuple[float, float]:
        icon_positions = {
            (True, 1): prepare.ICON_OPPONENT_SLOT,
            (True, 0): prepare.ICON_OPPONENT_DEFAULT,
            (False, 1): prepare.ICON_PLAYER_SLOT,
            (False, 0): prepare.ICON_PLAYER_DEFAULT,
        }
        return icon_positions[
            (
                monsters_in_play == self.monsters_in_play_left,
                monsters_in_play.index(monster),
            )
        ]

    def reset_status_icons(self) -> None:
        """
        Update/reset status icons for monsters.

        """
        # update huds
        for player in self.active_players:
            self.update_hud(player, False)
        # remove all status icons
        self.sprites.remove(*self._status_icons.values())
        self._status_icons.clear()

        # add status icons
        for monster in self.active_monsters:
            self._status_icons[monster] = []
            for status in monster.status:
                if status.icon:
                    icon_position = (
                        self.get_status_icon_position(
                            monster, self.monsters_in_play_left
                        )
                        if monster in self.monsters_in_play_left
                        else self.get_status_icon_position(
                            monster, self.monsters_in_play_right
                        )
                    )
                    cache_key = (status.icon, icon_position)
                    if cache_key not in self._status_icon_cache:
                        self._status_icon_cache[cache_key] = self.load_sprite(
                            status.icon, layer=200, center=icon_position
                        )

                    icon = self._status_icon_cache[cache_key]
                    self.sprites.add(icon, layer=200)
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
        state = self.client.push_state(
            self.graphics.menu, cmb=self, monster=monster
        )
        state.rect = self.calculate_menu_rectangle()

    def calculate_menu_rectangle(self) -> Rect:
        rect_screen = self.client.screen.get_rect()
        menu_width = rect_screen.w // 2.5
        menu_height = rect_screen.h // 4
        rect = Rect(0, 0, menu_width, menu_height)
        rect.bottomright = rect_screen.w, rect_screen.h
        return rect

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
        damage_map = DamageReport(attacker, defender, damage)
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
        self._action_queue.enqueue(action, self._turn)

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
        action_queue = self._action_queue.queue
        action_queue[:] = [
            action
            for action in action_queue
            if action.user is not monster and action.target is not monster
        ]

    def perform_action(
        self,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, Condition, None],
        target: Monster,
    ) -> None:
        """
        Perform the action.

        Parameters:
            user: Monster or NPC that does the action.
            method: Technique or item or condition used.
            target: Monster that receives the action.
        """
        if isinstance(method, Technique) and isinstance(user, Monster):
            self._handle_monster_technique(user, method, target)
        if isinstance(method, Item) and isinstance(user, NPC):
            self._handle_npc_item(user, method, target)
        if isinstance(method, Condition):
            self._handle_condition(method, target)

    def _handle_monster_technique(
        self,
        user: Monster,
        method: Technique,
        target: Monster,
    ) -> None:
        action_time = 0.0
        # action is performed, so now use sprites to animate it
        # this value will be None if the target is off screen
        target_sprite = self._monster_sprite_map.get(target, None)
        # slightly delay the monster shake, so technique animation
        # is synchronized with the damage shake motion
        hit_delay = 0.0
        # monster uses move
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
        self.play_sound_effect(method.sfx)
        # animation own_monster, technique doesn't tackle
        hit_delay += 0.5
        if method.target["own_monster"]:
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
                    "use_success" if result_tech["success"] else "use_failure"
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

        if result_tech["success"]:
            self.play_animation(
                method, target, target_sprite, action_time, is_flipped
            )

    def _handle_npc_item(
        self,
        user: NPC,
        method: Item,
        target: Monster,
    ) -> None:
        action_time = 0.0
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
            if method.behaviors.throwable:
                item = self.animate_throwing(target, method)
                self.task(item.kill, 1.5)
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
            self.play_animation(method, target, None, action_time)

        self.text_animations_queue.append(
            (partial(self.alert, message), action_time)
        )

    def _handle_condition(self, method: Condition, target: Monster) -> None:
        action_time = 0.0
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
        self.play_animation(method, target, None, action_time)

    def play_animation(
        self,
        method: Union[Technique, Condition, Item],
        target: Monster,
        target_sprite: Optional[Sprite],
        action_time: float,
        is_flipped: bool = False,
    ) -> None:
        """
        Play an animation for the given method and target.

        Parameters:
            method: The method to play the animation for.
            target: The target monster.
            target_sprite: The sprite for the target monster.
            action_time: The time to play the animation for.
            is_flipped: Whether the animation should be flipped.
        """
        if target_sprite is None:
            target_sprite = self._monster_sprite_map.get(target, None)

        animation = self._method_cache.get(method, is_flipped)

        if target_sprite and animation:
            animation.rect.center = target_sprite.rect.center
            assert animation.animation
            self.task(animation.animation.play, 0.6)
            self.task(partial(self.sprites.add, animation, layer=50), 0.6)
            self.task(animation.kill, action_time)

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

    def award_experience_and_money(self, monster: Monster) -> None:
        """
        Award experience and money to the winners.

        Parameters:
            monster: Monster that was fainted.

        """
        winners = get_winners(monster, self._damage_map)
        if winners:
            for winner in winners:
                # Award money and experience
                awarded_mon = award_money(monster, winner)
                awarded_exp = award_experience(
                    monster, winner, self._damage_map
                )

                if winner.owner and winner.owner.isplayer:
                    levels = winner.give_experience(awarded_exp)
                    if self.is_trainer_battle:
                        self._prize += awarded_mon
                else:
                    levels = 0

                # Log experience gain
                if winner.owner and winner.owner.isplayer:
                    params = {"name": winner.name.upper(), "xp": awarded_exp}
                    if self._xp_message is not None:
                        self._xp_message += "\n" + T.format(
                            "combat_gain_exp", params
                        )
                    else:
                        self._xp_message = T.format("combat_gain_exp", params)

                # Update HUD and handle level up
                self.update_hud_and_level_up(winner, levels)

    def update_hud_and_level_up(self, winner: Monster, levels: int) -> None:
        """
        Update the HUD and handle level ups for the winner.

        Parameters:
            winner: Monster that won the battle.
            levels: Number of levels gained.

        """
        if winner in self.monsters_in_play_right:
            new_techniques = winner.update_moves(levels)
            if new_techniques:
                tech_list = ", ".join(
                    tech.name.upper() for tech in new_techniques
                )
                params = {"name": winner.name.upper(), "tech": tech_list}
                mex = T.format("tuxemon_new_tech", params)
                if self._xp_message is not None:
                    self._xp_message += "\n" + mex
                else:
                    self._xp_message = mex
            if winner.owner and winner.owner.isplayer:
                self.task(partial(self.animate_exp, winner), 2.5)
                self.task(partial(self.delete_hud, winner), 3.2)
                self.task(partial(self.update_hud, winner.owner, False), 3.2)

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

        This method iterates over all monsters in the game, both friendly
        and enemy, and performs the following actions:
        - Animates the monster's HP display
        - Applies any status effects (e.g., poison, burn, etc.)
        - Checks if the monster has fainted and removes it from the game
            if so
        - Updates the experience bar for the player's monsters if an enemy
            monster has fainted

        * Monsters will be removed from play here
        """
        for monster_party in self.monsters_in_play.values():
            for monster in monster_party:
                self.animate_hp(monster)
                self.apply_status_effects(monster)
                if fainted(monster):
                    self.handle_monster_defeat(monster)

    def apply_status_effects(self, monster: Monster) -> None:
        """
        Applies any status effects to the given monster.

        Parameters:
            monster: Monster that was defeated.
        """
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

    def handle_monster_defeat(self, monster: Monster) -> None:
        """
        Handles the defeat of a monster, removing it from the game and
        updating the experience bar if necessary.

        Parameters:
            monster: Monster that was defeated.
        """
        self.remove_monster_actions_from_queue(monster)
        self.faint_monster(monster)
        self.award_experience_and_money(monster)
        # Remove monster from damage map
        self._damage_map = [
            element
            for element in self._damage_map
            if element.defense != monster and element.attack != monster
        ]

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
        self._action_queue.clear_queue()
        self._action_queue.clear_history()
        self._pending_queue = list()
        self._damage_map = list()

    def end_combat(self) -> None:
        """End the combat."""
        self.clean_combat()

        # fade music out
        self.client.current_music.stop()

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
