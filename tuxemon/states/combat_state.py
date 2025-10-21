# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
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
from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING, ClassVar, Optional, Union

from tuxemon import prepare
from tuxemon.ai import AIManager
from tuxemon.animation import Animation, Task
from tuxemon.animation_entity import AnimationManager
from tuxemon.combat.combat_context import CombatContext
from tuxemon.combat.machine import CombatMachine, CombatPhase
from tuxemon.combat.reward_system import RewardSystem
from tuxemon.combat.utils import (
    track_battles,
)
from tuxemon.db import (
    EffectPhase,
    ItemCategory,
    OutputBattle,
)
from tuxemon.formula import config_combat
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.state.state import State
from tuxemon.states.combat_animations import CombatAnimations
from tuxemon.states.monster_menu import MonsterMenuState
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique
from tuxemon.tools import assert_never
from tuxemon.ui.combat_notifier import CombatNotifier, TextAnimationManager
from tuxemon.ui.method_animation import MethodAnimationCache
from tuxemon.ui.text_alignment import HorizontalAlignment

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)


class WaitForInputState(State):
    """Just wait for input blocking everything"""

    name: ClassVar[str] = "WaitForInputState"

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

    name: ClassVar[str] = "CombatState"
    draw_borders = False
    escape_key_exits = False

    def __init__(self, context: CombatContext) -> None:
        self.phase: Optional[CombatPhase] = None
        self._method_cache = MethodAnimationCache(AnimationManager())
        self.text_anim = TextAnimationManager()
        self._decision_queue: list[Monster] = []
        # player => home areas on screen
        super().__init__(context=context)
        self.unregister_event_handlers()
        self.register_event_handlers()
        self.machine = CombatMachine(self.client.combat_session)
        self.client.combat_session.set_combat_type(context.combat_type)
        self.client.combat_session.set_battle_format(context.is_double_battle)
        self.client.combat_session.set_players(context.teams)
        self._lock_update = self.client.config.combat_click_to_continue
        self.show_combat_dialog()
        self.transition_phase(CombatPhase.BEGIN)
        self.task(
            partial(setattr, self, "phase", CombatPhase.READY), interval=3
        )
        self.ai_manager = AIManager(self.session)
        self.notifier = CombatNotifier(
            state=self,
            text_anim_manager=self.text_anim,
            alert_method=self.dialog.alert,
            lock_update=self._lock_update,
        )

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

    def update_combat_phase(self) -> None:
        """
        Update the combat phase.
        """
        if self.client.current_state:
            if self.client.current_state.name == "WaitForInputState":
                return
        time_left = self.text_anim.get_text_animation_time_left()
        if time_left <= 0 and all(map(self.is_task_finished, self.animations)):
            new_phase = self.machine.determine_next_phase(self.phase)
            if new_phase:
                self.phase = new_phase
                self.transition_phase(new_phase)
            self.update_phase()

    def update(self, time_delta: float) -> None:
        """
        Update the combat state.

        This method is responsible for updating the text animation and the combat phase.
        """
        super().update(time_delta)
        self.text_anim.update_text_animation(time_delta)
        self.update_combat_phase()

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
        c_session = self.client.combat_session

        if (
            phase == CombatPhase.BEGIN
            or phase == CombatPhase.READY
            or phase == CombatPhase.PRE_ACTION
        ):
            pass

        elif phase == CombatPhase.HOUSEKEEPING:
            c_session.next_turn()

            # fill all battlefield positions, but on round 1, don't ask
            c_session.fill_battlefield_positions(ask=c_session.turn > 1)
            c_session.track_enemy_monsters(self.session)

        elif phase == CombatPhase.DECISION:
            self.update_icons_for_monsters()
            self.animate_update_party_hud()
            c_session.check_decisions(self.session)
            if not self._decision_queue:
                c_session.initialize_hit_chances()
                self.process_player_decisions()

        elif phase == CombatPhase.ACTION:
            c_session.action_queue.sort()

        elif phase == CombatPhase.POST_ACTION:
            if c_session.action_queue.pending:
                c_session.action_queue.autoclean_pending()
                c_session.action_queue.from_pending_to_action(c_session.turn)
            c_session.apply_statuses(self.session)

        elif (
            phase == CombatPhase.RESOLVE_MATCH or phase == CombatPhase.RAN_AWAY
        ):
            pass

        elif phase == CombatPhase.DRAW_MATCH:
            message = self.track_battle_results(
                OutputBattle.draw, c_session.defeated_players
            )
            if message:
                self.process_combat_message(message)

        elif phase == CombatPhase.HAS_WINNER:
            message = self.track_battle_results(
                OutputBattle.won,
                c_session.remaining_players,
                c_session.defeated_players,
            )
            message += "\n" + self.track_battle_results(
                OutputBattle.lost,
                c_session.defeated_players,
                c_session.remaining_players,
            )
            if message:
                self.process_combat_message(message)

        elif phase == CombatPhase.END_COMBAT:
            self.end_combat()

        else:
            assert_never(phase)

    def update_phase(self) -> None:
        """
        Execute/update phase actions.

        Part of state machine
        * Do not change phase
        * Will be run each iteration phase is active
        * Do not test conditions to change phase
        """
        if self.phase == CombatPhase.DECISION:
            # show monster action menu for human players
            if self._decision_queue:
                if self.client.combat_session.is_double:
                    self.handle_pending_actions(self._decision_queue, 2)
                else:
                    self.handle_pending_actions(self._decision_queue, 1)

        elif self.phase == CombatPhase.ACTION:
            self.handle_action_queue()

        elif self.phase == CombatPhase.POST_ACTION:
            self.handle_action_queue()

    def handle_pending_actions(
        self, pending_monsters: list[Monster], num_actions: int
    ) -> None:
        actual_actions = min(num_actions, len(pending_monsters))
        logger.debug(f"Handling {actual_actions} pending monster action(s)")

        for i in range(actual_actions):
            monster = pending_monsters.pop(0)
            logger.debug(f"Processing monster #{i + 1}: {monster.name}")
            monster.moves.recharge_moves()
            self.show_monster_action_menu(monster)

    def handle_action_queue(self) -> None:
        """Take one action from the queue and do it."""
        if not self.client.combat_session.action_queue.is_empty():
            action = self.client.combat_session.action_queue.pop()
            self.perform_action(action.user, action.method, action.target)
            self.task(self.check_party_hp, interval=1)
            self.task(self.animate_party_status, interval=3)
            self.notifier.trigger_xp_and_wait_for_input()

    def ask_player_for_monster(self, player: NPC) -> None:
        """
        Open dialog to allow player to choose a Tuxemon to enter into play.

        Parameters:
            player: Player who has to select a Tuxemon.
        """

        def add(menuitem: MenuItem[Monster]) -> None:
            monster = menuitem.game_object
            self.client.combat_session.add_monster_into_play(
                self.session, player, monster
            )
            self.client.remove_state_by_name("MonsterMenuState")

        def validate(menu_item: MenuItem[Monster]) -> bool:
            if isinstance(menu_item, Monster):
                if menu_item.is_fainted:
                    return False
                if menu_item in self.client.combat_session.active_monsters:
                    return False
                return True
            return False

        state = self.client.push_state(MonsterMenuState(player.monsters))
        # must use a partial because alert relies on a text box that may not
        # exist until after the state hs been startup
        state.task(
            partial(state.dialog.alert, T.translate("combat_replacement")),
            interval=0,
        )
        state.is_valid_entry = validate  # type: ignore[assignment]
        state.on_menu_selection = add  # type: ignore[assignment]
        state.escape_key_exits = False

    def handle_monster_entry(
        self,
        player: NPC,
        monster: Monster,
    ) -> None:
        """
        Handles visual and UI updates when a monster is added to the battlefield.

        Parameters:
            player: The player adding the monster.
            monster: The monster being added.
        """
        # Get capture device sprite
        capture_device = Item.create(monster.capture_device)
        sprite = self._method_cache.get(capture_device, False)
        if not sprite:
            raise ValueError(f"Sprite not found for item {capture_device}")

        # Animate release and update HUD
        self.animate_monster_release(player, monster, sprite)
        self.update_hud(player, True, True)

        # Show combat swap message if not first turn
        if self.client.combat_session.turn > 1:
            message = self.client.combat_session.get_message_swap(
                player, monster
            )
            self.text_anim.add_text_animation(
                partial(self.dialog.alert, message), 0
            )

    def update_icons_for_monsters(self) -> None:
        """Update/reset status icons for monsters."""
        self.status_icons.update_icons_for_monsters(
            self.client.combat_session.active_monsters,
        )

    def show_monster_action_menu(self, monster: Monster) -> None:
        """
        Show the main window for choosing player actions.

        Parameters:
            monster: Monster to choose an action for.
        """
        self.client.push_state(
            self.graphics.menu, session=self.session, cmb=self, monster=monster
        )

    def process_combat_message(self, message: str) -> None:
        """
        Handles combat messages by triggering text animation and blocking input
        until the message has been processed.
        """
        self.notifier.show_message_and_wait_for_input(message)

    def track_battle_results(
        self,
        result_type: OutputBattle,
        players: Sequence[NPC],
        opponents: Optional[Sequence[NPC]] = None,
    ) -> str:
        """
        Tracks battle results based on the given type (draw, won, lost).

        If `result_type` is "draw", all players are recorded as tied.
        If `result_type` is "won" or "lost", winners and losers are recorded accordingly.
        """
        message = ""
        for player in players:
            message += ("\n" if message else "") + track_battles(
                session=self.session,
                output=result_type,
                character=player,
                opponents=opponents if opponents else players,
                turns=self.client.combat_session.turn,
                combat_type=self.client.combat_session.combat_type,
                prize=(
                    self.client.combat_session.prize
                    if result_type == OutputBattle.won
                    else 0
                ),
            )
        return message

    def process_player_decisions(self) -> None:
        """
        Updates HUD and assigns monsters to the decision queue for players,
        while recharging moves and triggering AI actions for NPCs.
        """
        self._decision_queue = []

        for monster in self.client.combat_session.active_monsters:
            char = (
                self.client.combat_session.field_monsters.get_npc_for_monster(
                    monster
                )
            )
            monster.moves.recharge_moves()
            if char in self.client.combat_session.human_players:
                # Still add to queue for menu interaction
                self._decision_queue.append(monster)
            else:
                # Ask AIManager to handle the decision for this monster
                self.ai_manager.process_ai_turn(monster, char)

        # Start the menu flow for human players
        if self._decision_queue:
            self.show_monster_action_menu(self._decision_queue.pop(0))

    def remove_monster_from_play(self, monster: Monster) -> None:
        """
        Remove monster from play without fainting it.

        * If another monster has targeted this monster, it can change action
        * Will remove actions as well
        * currently for 'swap' technique
        """
        self.client.combat_session.swap_tracker.clear()
        self.remove_monster_actions_from_queue(monster)
        self.animate_monster_faint(monster)

    def remove_monster_actions_from_queue(self, monster: Monster) -> None:
        """
        Remove all queued actions for a particular monster.

        This is used mainly for removing actions after monster is fainted.

        Parameters:
            monster: Monster whose actions will be removed.
        """
        self.hud_manager.unassign(monster.get_owner(), monster)
        self.status_icons.recalculate_icon_positions()
        action_queue = self.client.combat_session.action_queue.queue
        action_queue[:] = [
            action
            for action in action_queue
            if action.user is not monster and action.target is not monster
        ]
        self.ai_manager.remove_ai(monster)

    def perform_action(
        self,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, Status, None],
        target: Monster,
    ) -> None:
        """
        Perform the action.

        Parameters:
            user: Monster or NPC that does the action.
            method: Technique or item or status used.
            target: Monster that receives the action.
        """
        if isinstance(method, Technique) and isinstance(user, Monster):
            self._handle_monster_technique(user, method, target)
        if isinstance(method, Item) and isinstance(user, NPC):
            self._handle_npc_item(user, method, target)
        if isinstance(method, Status):
            self._handle_status(method, target)

    def _handle_monster_technique(
        self,
        user: Monster,
        method: Technique,
        target: Monster,
    ) -> None:
        action_time = 0.0
        # animate action; target sprite is None if off-screen
        target_sprite = self.sprite_map.get_sprite(target)
        # slightly delay the monster shake, so technique animation
        # is synchronized with the damage shake motion
        hit_delay = 0.0
        # monster uses move
        result_tech, status_result = (
            self.client.combat_session.apply_technique(
                self.session, method, user, target
            )
        )
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
        if status_result:
            if status_result.extras:
                templates = [
                    T.translate(extra) for extra in status_result.extras
                ]
                template = "\n".join(templates)
                message += "\n" + template
            if status_result.statuses:
                status = random.choice(status_result.statuses)
                user.status.apply_status(self.session, status)

        if result_tech.success and method.use_success:
            template = getattr(method, "use_success")
            m = T.format(template, context)
        elif not result_tech.success and method.use_failure:
            template = getattr(method, "use_failure")
            m = T.format(template, context)
        else:
            m = None

        if result_tech.extras:
            extra_tmpls = [T.translate(extra) for extra in result_tech.extras]
            tmpl = "\n".join(extra_tmpls)
            m = (m or "") + ("\n" + tmpl if m else tmpl)

        if m:
            message += "\n" + m
            action_time += self.text_anim.compute_text_anim_time(message)

        self.play_sound_effect(method.sfx)
        # animation own_monster, technique doesn't tackle
        hit_delay += 0.5
        if method.target["own_monster"]:
            target_sprite = self.sprite_map.get_sprite(user)

        if result_tech.should_tackle:
            user_sprite = self.sprite_map.get_sprite(user)

            if user_sprite:
                self.animate_sprite_tackle(user_sprite)

            if target_sprite:
                self.task(
                    partial(
                        self.animate_sprite_take_damage,
                        target_sprite,
                    ),
                    interval=hit_delay + 0.2,
                )
                self.task(
                    partial(self.blink, target_sprite),
                    interval=hit_delay + 0.6,
                )

            self.client.combat_session.enqueue_damage(
                user, target, result_tech.damage
            )

            plague = user.plague.get_most_severe_plague_slug()
            if plague:
                m = user.plague.get_suppressed_symptom_message(
                    user.name, plague
                )
                if m:
                    message += "\n" + m

            if method.range != "special":
                element_damage_key = config_combat.multiplier_map.get(
                    result_tech.element_multiplier
                )
                if element_damage_key:
                    m = T.translate(element_damage_key)
                    message += "\n" + m
                    action_time += self.text_anim.compute_text_anim_time(
                        message
                    )

        self.text_anim.add_text_animation(
            partial(self.dialog.alert, message), action_time
        )

        is_flipped = False
        for trainer in self.client.combat_session.ai_players:
            if user in self.client.combat_session.field_monsters.get_monsters(
                trainer
            ):
                is_flipped = True
                break

        if result_tech.success:
            self.play_animation(
                method, target, target_sprite, action_time, is_flipped
            )

    def _handle_npc_item(
        self,
        user: NPC,
        item: Item,
        target: Monster,
    ) -> None:
        action_time = 0.0
        result_item = self.client.combat_session.apply_item(
            self.session, item, user, target
        )
        context = {
            "user": user.name,
            "name": item.name,
            "target": target.name,
        }
        message = T.format(item.use_item, context)
        # animation sprite
        item_sprite = self._method_cache.get(item, False)
        # handle the capture device
        if item.category == ItemCategory.capture and item_sprite:
            # retrieve tuxeball
            message += "\n" + T.translate("attempting_capture")
            action_time = result_item.num_shakes + 1.8

            success_header_text = ""
            if result_item.success:
                success_header_text = T.translate("gotcha")
                if len(user.monsters) >= prepare.PARTY_LIMIT:
                    success_text = T.format(
                        "gotcha_kennel", {"name": target.name.upper()}
                    )
                else:
                    success_text = T.format(
                        "gotcha_team", {"name": target.name.upper()}
                    )
                failure_text = ""
            else:
                success_text = ""
                failure_text = T.translate(
                    f"captured_failed_{result_item.num_shakes}"
                )

            self.animate_capture_monster(
                result_item,
                target,
                item,
                item_sprite,
                (success_header_text, success_text, failure_text),
            )
        else:
            if item.behaviors.throwable:
                sprite = self.animate_throwing(target, item)
                self.task(sprite.kill, interval=1.5)
            msg_type = "use_success" if result_item.success else "use_failure"
            template = getattr(item, msg_type)
            tmpl = T.format(template, context)
            # extra output
            if result_item.extras:
                extra_tmpls = [
                    T.translate(extra) for extra in result_item.extras
                ]
                tmpl = "\n".join(extra_tmpls)
            if template:
                message += "\n" + tmpl
                action_time += self.text_anim.compute_text_anim_time(message)
            self.play_animation(item, target, None, action_time)

        self.text_anim.add_text_animation(
            partial(self.dialog.alert, message), action_time
        )

    def _handle_status(self, status: Status, target: Monster) -> None:
        action_time = 0.0
        result = self.client.combat_session.apply_status(
            self.session, status, target, EffectPhase.PERFORM_STATUS
        )
        context = {
            "name": status.name,
            "target": target.name,
        }
        message: str = ""
        # successful statuses
        if result.success:
            if status.use_success:
                template = getattr(status, "use_success")
                message = T.format(template, context)
            # first turn status
            if status.nr_turn == 1 and status.gain_cond:
                first_turn = getattr(status, "gain_cond")
                first = T.format(first_turn, context)
                message = first + "\n" + message
        # not successful statuses
        if not result.success:
            if status.use_failure:
                template = getattr(status, "use_failure")
                message = T.format(template, context)
        if result.extras:
            templates = [T.translate(extra) for extra in result.extras]
            message = message + "\n" + "\n".join(templates)
        if message:
            action_time += self.text_anim.compute_text_anim_time(message)
            self.text_anim.add_text_animation(
                partial(self.dialog.alert, message), action_time
            )
        self.play_animation(status, target, None, action_time)

    def play_animation(
        self,
        method: Union[Technique, Status, Item],
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
            target_sprite = self.sprite_map.get_sprite(target)

        animation = self._method_cache.get(method, is_flipped)

        if target_sprite and animation:
            animation.rect.center = target_sprite.rect.center
            assert animation.animation
            start_delay = 0.6
            self.task(animation.animation.play, interval=start_delay)
            self.task(
                partial(self.sprites.add, animation, layer=50),
                interval=start_delay,
            )
            safe_action_time = max(
                action_time, animation.animation.duration + start_delay
            )
            self.task(animation.kill, interval=safe_action_time)

    def award_experience_and_money(self, monster: Monster) -> None:
        """
        Award experience and money to the winners.

        Parameters:
            monster: Monster that was fainted.
        """
        damage_map = self.client.combat_session.damage_tracker
        reward_system = RewardSystem(self.session, damage_map)
        reward_system.apply_penalties(monster)
        rewards = reward_system.award_rewards(monster)

        for data in rewards.winners:
            if data.levels_gained > 0:
                self.monsters_just_leveled_up[data.winner.slug] = True

        # Update combat state with rewards
        self.client.combat_session.add_prize(rewards.prize)
        for message in rewards.messages:
            self.text_anim.add_xp_message(message)

        if rewards.update:
            self.update_hud_and_level_up(
                rewards.winners[0].winner, rewards.moves
            )

    def update_hud_and_level_up(
        self, winner: Monster, techniques: list[Technique]
    ) -> None:
        """
        Update the HUD and handle level ups for the winner.

        Parameters:
            winner: Monster that won the battle.
            techniques: List of learned techniques.
        """
        if winner in self.client.combat_session.monsters_in_play_right:
            if techniques:
                tech_list = ", ".join(tech.name.upper() for tech in techniques)
                params = {"name": winner.name.upper(), "tech": tech_list}
                mex = T.format("tuxemon_new_tech", params)
                self.text_anim.add_xp_message(mex)
            owner = winner.get_owner()
            if owner.is_player:
                self.task(partial(self.animate_exp, winner), interval=2.5)
                self.task(
                    partial(self.update_hud, owner, False, True), interval=4.0
                )

    def animate_party_status(self) -> None:
        """
        Animate monsters that need to be fainted.

        * Animation to remove monster is handled here
        TODO: check for faint status, not HP
        """
        for (
            _,
            party,
        ) in (
            self.client.combat_session.field_monsters.get_all_monsters().items()
        ):
            for monster in party:
                if monster.is_fainted:
                    params = {"name": monster.name.upper()}
                    msg = T.format("combat_fainted", params)
                    self.text_anim.add_text_animation(
                        partial(self.dialog.alert, msg),
                        config_combat.action_time,
                    )
                    self.animate_monster_faint(monster)

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
        for (
            monster_party
        ) in (
            self.client.combat_session.field_monsters.get_all_monsters().values()
        ):
            for monster in monster_party:
                self.animate_hp(monster)
                self.apply_status_effects(monster)
                if monster.is_fainted:
                    self.handle_monster_defeat(monster)

    def apply_status_effects(self, monster: Monster) -> None:
        """
        Applies any status effects to the given monster.

        Parameters:
            monster: Monster that was defeated.
        """
        status = monster.status.get_current_status()
        if status:
            result_status = status.use(
                self.session, EffectPhase.CHECK_PARTY_HP
            )
            if result_status.extras:
                templates = [
                    T.translate(extra) for extra in result_status.extras
                ]
                extra = "\n".join(templates)
                action_time = self.text_anim.compute_text_anim_time(extra)
                self.text_anim.add_text_animation(
                    partial(self.dialog.alert, extra), action_time
                )

    def handle_monster_defeat(self, monster: Monster) -> None:
        """
        Handles the defeat of a monster, removing it from the game and
        updating the experience bar if necessary.

        Parameters:
            monster: Monster that was defeated.
        """
        self.remove_monster_actions_from_queue(monster)
        self.award_experience_and_money(monster)
        # Remove monster from damage map
        self.client.combat_session.damage_tracker.remove_monster(monster)

    def clean_combat(self) -> None:
        """Clean combat."""
        for player in self.client.combat_session.players:
            for mon in player.monsters:
                # reset status stats
                mon.set_stats()
                mon.end_combat(self.session)
                # reset type
                mon.types.reset_to_default()
                # reset technique stats
                mon.moves.set_stats()

        self.ai_manager.clear_ai()

    def clear_combat_states(self) -> None:
        """
        Removes any states stacked on top of the combat state
        """
        while not isinstance(self.client.current_state, CombatState):
            self.client.pop_state()

    def end_combat(self) -> None:
        """End the combat."""
        self.clean_combat()
        new_entry = self.client.combat_session.get_variable("new_tuxepedia")
        new_monster = self.client.combat_session.get_variable("captured_mon")
        self.client.combat_session.reset()
        self.unregister_event_handlers()
        self.client.current_music.stop()
        self.clear_combat_states()
        self.phase = None

        if new_entry and new_monster:
            self.client.remove_state_by_name("CombatState")
            params = {"monster": new_monster, "source": self.name}
            self.client.push_state("MonsterInfoState", kwargs=params)
        else:
            self.client.push_state("FadeOutTransition", caller=self)

    def unregister_event_handlers(self) -> None:
        """
        Unregisters all event bus handlers for combat-related events.
        """
        if not hasattr(self.client, "event_bus"):
            raise RuntimeError("Client event bus is not initialized")

        event_bus = self.client.event_bus
        event_bus.unsubscribe(
            "monster_disappeared", self._on_monster_disappeared
        )
        event_bus.unsubscribe("monster_appeared", self._on_monster_appeared)
        event_bus.unsubscribe(
            "monster_swapped_out", self._on_monster_swapped_out
        )
        event_bus.unsubscribe(
            "monster_swapped_in", self._on_monster_swapped_in
        )
        event_bus.unsubscribe("mirror_effect", self._on_mirror_effect)
        event_bus.unsubscribe("status_applied", self._on_status_applied)
        event_bus.unsubscribe("update_party_hud", self._on_update_party_hud)
        event_bus.unsubscribe("clean_combat", self._on_clean_combat)
        event_bus.unsubscribe("monster_needed", self._on_monster_needed)
        event_bus.unsubscribe(
            "update_sprite_position", self._on_update_sprite_position
        )
        event_bus.unsubscribe("monster_added", self._on_monster_added)

    def register_event_handlers(self) -> None:
        """
        Registers all event bus handlers for combat-related events.
        """
        if not hasattr(self.client, "event_bus"):
            raise RuntimeError("Client event bus is not initialized")

        event_bus = self.client.event_bus
        event_bus.subscribe(
            "monster_disappeared", self._on_monster_disappeared
        )
        event_bus.subscribe("monster_appeared", self._on_monster_appeared)
        event_bus.subscribe(
            "monster_swapped_out", self._on_monster_swapped_out
        )
        event_bus.subscribe("monster_swapped_in", self._on_monster_swapped_in)
        event_bus.subscribe("mirror_effect", self._on_mirror_effect)
        event_bus.subscribe("status_applied", self._on_status_applied)
        event_bus.subscribe("update_party_hud", self._on_update_party_hud)
        event_bus.subscribe("clean_combat", self._on_clean_combat)
        event_bus.subscribe("monster_needed", self._on_monster_needed)
        event_bus.subscribe(
            "update_sprite_position", self._on_update_sprite_position
        )
        event_bus.subscribe("monster_added", self._on_monster_added)

    def _on_monster_added(
        self,
        player: NPC,
        monster: Monster,
        removed: Optional[Monster] = None,
    ) -> None:
        self.handle_monster_entry(player, monster)

    def _on_monster_needed(self, player: NPC, ask: bool = False) -> None:
        session = self.client.combat_session
        if player in session.human_players and ask:
            self.ask_player_for_monster(player)
        else:
            replacement = self.ai_manager.choose_replacement_monster(player)
            if replacement:
                session.add_monster_into_play(
                    self.session, player, replacement
                )

    def _on_update_sprite_position(
        self, player: NPC, monster: Monster
    ) -> None:
        new_feet = self.hud_manager.get_feet_position(player, monster)
        self.sprite_map.update_sprite_position(monster, new_feet)

    def _on_clean_combat(self) -> None:
        self.clean_combat()

    def _on_status_applied(self) -> None:
        self.update_icons_for_monsters()

    def _on_update_party_hud(self) -> None:
        self.animate_update_party_hud()

    def _on_monster_disappeared(self, user: Monster) -> None:
        user_sprite = self.sprite_map.get_sprite(user)
        if user_sprite and user_sprite.is_visible():
            user_sprite.toggle_visible()

    def _on_monster_appeared(self, user: Monster) -> None:
        user_sprite = self.sprite_map.get_sprite(user)
        if user_sprite and not user_sprite.is_visible():
            user_sprite.toggle_visible()

    def _on_monster_swapped_out(self, monster: Monster) -> None:
        self.remove_monster_from_play(monster)
        logger.debug(f"{monster.name} removed from play")

    def _on_monster_swapped_in(
        self, removed: Monster, added: Monster, player: NPC
    ) -> None:
        def swap_add() -> None:
            logger.debug(
                f"Swap add triggered: replacing {removed.name} with {added.name}"
            )
            self.client.combat_session.add_monster_into_play(
                self.session, player, added, removed
            )

        self.task(partial(swap_add), interval=0.75)

    def _on_mirror_effect(
        self, user: Monster, target: Monster, direction: str
    ) -> None:
        """
        Handles the UI logic for a mirror effect.
        This method is a subscriber to the 'mirror_effect' event.

        Direction values:
        - "both": Swap both user and target sprites.
        - "user_to_target": Replace target sprite with user-facing sprite.
        - "target_to_user": Replace user sprite with target-facing sprite.
        """
        user_sprite = self.sprite_map.get_sprite(user)
        target_sprite = self.sprite_map.get_sprite(target)

        assert user_sprite and target_sprite

        if direction == "both":
            front_user = user.get_sprite(
                "front", midbottom=target_sprite.rect.midbottom
            )
            back_target = target.get_sprite(
                "back", midbottom=user_sprite.rect.midbottom
            )
            self.sprites.add(front_user)
            self.sprites.add(back_target)
            self.sprite_map.add_sprite(user, back_target)
            self.sprite_map.add_sprite(target, front_user)
            self.sprites.remove(user_sprite)
            self.sprites.remove(target_sprite)

        elif direction == "user_to_target":
            _, h_align = self.combat_zone.get_zone(user_sprite.rect)
            side = "front" if h_align is HorizontalAlignment.LEFT else "back"

            front_user = user.get_sprite(
                side, midbottom=target_sprite.rect.midbottom
            )
            self.sprites.add(front_user)
            self.sprite_map.add_sprite(target, front_user)
            self.sprites.remove(target_sprite)

        elif direction == "target_to_user":
            _, h_align = self.combat_zone.get_zone(user_sprite.rect)
            side = "back" if h_align is HorizontalAlignment.LEFT else "front"

            back_target = target.get_sprite(
                side, midbottom=user_sprite.rect.midbottom
            )
            self.sprites.add(back_target)
            self.sprite_map.add_sprite(user, back_target)
            self.sprites.remove(user_sprite)
