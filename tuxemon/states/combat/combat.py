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
from collections.abc import Iterable, Sequence
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Any, Optional, Union

from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon import graphics
from tuxemon.ai import AIManager
from tuxemon.animation import Animation, Task
from tuxemon.combat import (
    alive_party,
    battlefield,
    defeated,
    get_awake_monsters,
    set_var,
    track_battles,
)
from tuxemon.db import (
    EffectPhase,
    ItemCategory,
    TargetType,
)
from tuxemon.formula import config_combat
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.state.state import State
from tuxemon.states.monster import MonsterMenuState
from tuxemon.status.status import Status
from tuxemon.technique.technique import Technique
from tuxemon.tools import assert_never
from tuxemon.ui.combat_notifier import CombatNotifier, TextAnimationManager
from tuxemon.ui.combat_swap import SwapTracker
from tuxemon.ui.graphic_box import GraphicBox
from tuxemon.ui.text import TextArea

from .combat_animations import CombatAnimations
from .combat_classes import (
    ActionQueue,
    DamageTracker,
    EnqueuedAction,
    MenuVisibility,
    MethodAnimationCache,
)
from .combat_context import CombatContext
from .reward_system import RewardSystem

if TYPE_CHECKING:
    from tuxemon.platform.events import PlayerInput
    from tuxemon.sprite import Sprite

logger = logging.getLogger(__name__)


class CombatPhase(Enum):
    BEGIN = "begin"
    READY = "ready"
    HOUSEKEEPING = "housekeeping"
    DECISION = "decision"
    PRE_ACTION = "pre_action"
    ACTION = "action"
    POST_ACTION = "post_action"
    RESOLVE_MATCH = "resolve_match"
    RAN_AWAY = "ran_away"
    DRAW_MATCH = "draw_match"
    HAS_WINNER = "has_winner"
    END_COMBAT = "end_combat"


class WaitForInputState(State):
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

    def __init__(self, context: CombatContext) -> None:
        self.phase: Optional[CombatPhase] = None
        self._damage_map = DamageTracker()
        self._method_cache = MethodAnimationCache()
        self._action_queue = ActionQueue()
        self.text_anim = TextAnimationManager()
        self._decision_queue: list[Monster] = []
        # player => home areas on screen
        self._turn: int = 0
        self._prize: int = 0
        self._captured_mon: Optional[Monster] = None
        self._new_tuxepedia: bool = False
        self._run: bool = False
        self._post_animation_task: Optional[Task] = None
        self._max_positions: dict[NPC, int] = {}
        self._random_tech_hit: dict[Monster, float] = {}
        self._combat_variables: dict[str, Any] = {}
        self._menu_visibility = MenuVisibility()

        super().__init__(context=context)
        self._lock_update = self.client.config.combat_click_to_continue
        self.is_trainer_battle = context.combat_type == "trainer"
        self.show_combat_dialog()
        self.transition_phase(CombatPhase.BEGIN)
        self.task(
            partial(setattr, self, "phase", CombatPhase.READY), interval=3
        )
        self.ai_manager = AIManager(self.session, self)
        self.swap_tracker = SwapTracker()
        self.notifier = CombatNotifier(
            state=self,
            text_anim_manager=self.text_anim,
            alert_method=self.alert,
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
            new_phase = self.determine_phase(self.phase)
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

    def draw(self, surface: Surface) -> None:
        """
        Draw combat state.

        Parameters:
            surface: Surface where to draw.
        """
        super().draw(surface)
        self.bars.draw_bars(self.hud_manager.hud_map)

    def determine_phase(
        self, phase: Optional[CombatPhase]
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
        if phase is None or phase == CombatPhase.BEGIN:
            return None

        elif phase == CombatPhase.READY:
            return CombatPhase.HOUSEKEEPING

        elif phase == CombatPhase.HOUSEKEEPING:
            # this will wait for players to fill battleground positions
            for player in self.active_players:
                positions_available = self.get_available_positions(player)
                if positions_available:
                    return None
            return CombatPhase.DECISION

        elif phase == CombatPhase.DECISION:
            # TODO: only works for single player and if player runs
            if len(self.remaining_players) == 1:
                return CombatPhase.RAN_AWAY

            # assume each monster executes one action
            # if number of actions == monsters, then all monsters are ready
            elif len(self._action_queue.queue) == len(self.active_monsters):
                return CombatPhase.PRE_ACTION

            return None

        elif phase == CombatPhase.PRE_ACTION:
            return CombatPhase.ACTION

        elif phase == CombatPhase.ACTION:
            if self._action_queue.is_empty():
                return CombatPhase.POST_ACTION

            return None

        elif phase == CombatPhase.POST_ACTION:
            if self._action_queue.is_empty():
                return CombatPhase.RESOLVE_MATCH

            return None

        elif phase == CombatPhase.RESOLVE_MATCH:
            remaining = len(self.remaining_players)

            if remaining == 0:
                return CombatPhase.DRAW_MATCH
            elif remaining == 1:
                if self._run:
                    return CombatPhase.RAN_AWAY
                else:
                    return CombatPhase.HAS_WINNER
            else:
                return CombatPhase.HOUSEKEEPING

        elif phase == CombatPhase.RAN_AWAY:
            return CombatPhase.END_COMBAT

        elif phase == CombatPhase.DRAW_MATCH:
            return CombatPhase.END_COMBAT

        elif phase == CombatPhase.HAS_WINNER:
            return CombatPhase.END_COMBAT

        elif phase == CombatPhase.END_COMBAT:
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
        if (
            phase == CombatPhase.BEGIN
            or phase == CombatPhase.READY
            or phase == CombatPhase.PRE_ACTION
        ):
            pass

        elif phase == CombatPhase.HOUSEKEEPING:
            self._turn += 1
            # fill all battlefield positions, but on round 1, don't ask
            self.fill_battlefield_positions(ask=self._turn > 1)
            self.track_enemy_monsters()

        elif phase == CombatPhase.DECISION:
            self.update_icons_for_monsters()
            self.animate_update_party_hud()
            self.check_decisions()
            if not self._decision_queue:
                self.initialize_hit_chances()
                self.process_player_decisions()

        elif phase == CombatPhase.ACTION:
            self._action_queue.sort()

        elif phase == CombatPhase.POST_ACTION:
            if self._action_queue.pending:
                self._action_queue.autoclean_pending()
                self._action_queue.from_pending_to_action(self._turn)
            self.apply_statuses()

        elif (
            phase == CombatPhase.RESOLVE_MATCH or phase == CombatPhase.RAN_AWAY
        ):
            pass

        elif phase == CombatPhase.DRAW_MATCH:
            message = self.track_battle_results("draw", self.defeated_players)
            if message:
                self.process_combat_message(message)

        elif phase == CombatPhase.HAS_WINNER:
            message = self.track_battle_results(
                "won", self.remaining_players, self.defeated_players
            )
            message += "\n" + self.track_battle_results(
                "lost", self.defeated_players, self.remaining_players
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
                if self.is_double:
                    self.handle_double_action(self._decision_queue)
                else:
                    self.handle_single_action(self._decision_queue)

        elif self.phase == CombatPhase.ACTION:
            self.handle_action_queue()

        elif self.phase == CombatPhase.POST_ACTION:
            self.handle_action_queue()

    def handle_single_action(self, pending_monsters: list[Monster]) -> None:
        if pending_monsters:
            monster = pending_monsters.pop(0)
            monster.moves.recharge_moves()
            self.show_monster_action_menu(monster)

    def handle_double_action(self, pending_monsters: list[Monster]) -> None:
        if len(pending_monsters) >= 2:
            monster1 = pending_monsters.pop(0)
            monster1.moves.recharge_moves()
            self.show_monster_action_menu(monster1)
            monster2 = pending_monsters.pop(0)
            monster2.moves.recharge_moves()
            self.show_monster_action_menu(monster2)
        elif pending_monsters:
            self.handle_single_action(pending_monsters)

    def handle_action_queue(self) -> None:
        """Take one action from the queue and do it."""
        if not self._action_queue.is_empty():
            action = self._action_queue.pop()
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
            self.add_monster_into_play(player, monster)
            self.client.remove_state_by_name("MonsterMenuState")

        def validate(menu_item: MenuItem[Monster]) -> bool:
            if isinstance(menu_item, Monster):
                if menu_item.is_fainted:
                    return False
                if menu_item in self.active_monsters:
                    return False
                return True
            return False

        state = self.client.push_state(MonsterMenuState(player))
        # must use a partial because alert relies on a text box that may not
        # exist until after the state hs been startup
        state.task(
            partial(state.alert, T.translate("combat_replacement")), interval=0
        )
        state.is_valid_entry = validate  # type: ignore[assignment]
        state.on_menu_selection = add  # type: ignore[assignment]
        state.escape_key_exits = False

    def get_max_positions(self, player: NPC) -> int:
        """
        Calculates the maximum number of positions for a player based on
        their party size and battle mode.
        """
        if len(alive_party(player)) == 1:
            return 1
        return 2 if self.is_double else 1

    def get_available_positions(self, player: NPC) -> int:
        """
        Returns the number of available positions for a player on the battlefield.
        """
        max_positions = self.get_max_positions(player)
        on_the_field = len(self.field_monsters.get_monsters(player))
        return max_positions - on_the_field

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

            max_positions = self.get_max_positions(player)
            self._max_positions[player] = max_positions

            if max_positions == 1 and self.is_double:
                on_the_field = self.field_monsters.get_monsters(player)
                if on_the_field:
                    monster = on_the_field[0]
                    new_feet = self.hud_manager.get_feet_position(
                        player, monster
                    )
                    self.sprite_map.update_sprite_position(monster, new_feet)

            positions_available = self.get_available_positions(player)
            if positions_available:
                monsters = self.field_monsters.get_monsters(player)
                available = get_awake_monsters(player, monsters, self._turn)
                for _ in range(positions_available):
                    if player in humans and ask:
                        self.ask_player_for_monster(player)
                    else:
                        monster = next(available)
                        self.add_monster_into_play(player, monster)
                        self.update_tuxepedia(player, monster)

    def update_tuxepedia(self, player: NPC, monster: Monster) -> None:
        """
        Updates the tuxepedia for human players when a monster is encountered.

        Parameters:
            player: The player who encountered the monster.
            monster: The monster that was encountered.
        """
        for other_player in self.players:
            if other_player.isplayer and other_player != player:
                if monster.slug not in self._combat_variables:
                    other_player.tuxepedia.add_entry(monster.slug)
                    self._combat_variables[monster.slug] = True

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
        capture_device = Item.create(monster.capture_device)
        sprite = self._method_cache.get(capture_device, False)
        if not sprite:
            raise ValueError(f"Sprite not found for item {capture_device}")

        self.field_monsters.add_monster(player, monster)
        self.animate_monster_release(player, monster, sprite)
        self.update_hud(player, True, True)

        # Remove "bond" status from all active monsters
        for mon in self.active_monsters:
            mon.status.remove_bonded_statuses()

        # Handle new entry and removed monster's status effects
        phase = EffectPhase.SWAP_MONSTER
        status = monster.status.get_current_status()
        if status:
            status.execute_status_action(self.session, self, monster, phase)
        if removed is not None:
            r_status = removed.status.get_current_status()
            if r_status:
                r_status.execute_status_action(
                    self.session, self, removed, phase
                )

        # Create message for combat swap
        format_params = {
            "target": monster.name.upper(),
            "user": player.name.upper(),
        }
        if self._turn > 1:
            message = T.format("combat_swap", format_params)
            self.text_anim.add_text_animation(partial(self.alert, message), 0)

    def update_icons_for_monsters(self) -> None:
        """Update/reset status icons for monsters."""
        self.status_icons.update_icons_for_monsters(
            self.active_monsters,
        )

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
        result_type: str,
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
                player=player,
                players=opponents if opponents else players,
                prize=self._prize if result_type == "won" else 0,
                trainer_battle=self.is_trainer_battle,
            )
        return message

    def track_enemy_monsters(self) -> None:
        """
        Records properties of enemy monsters that participated in battle.
        """
        for player in self.remaining_players:
            monsters = self.field_monsters.get_monsters(player)
            if monsters and not player.isplayer:
                for mon in monsters:
                    battlefield(self.session, mon)

    def process_player_decisions(self) -> None:
        """
        Updates HUD and assigns monsters to the decision queue for players,
        while recharging moves and triggering AI actions for NPCs.
        """
        for player in list(self.active_players):
            self.update_hud(player, False, False)
            monsters = self.field_monsters.get_monsters(player)
            for monster in monsters:
                if player in self.human_players:
                    self._decision_queue.append(monster)
                else:
                    monster.moves.recharge_moves()
                    self.ai_manager.process_ai_turn(monster, player)

    def check_decisions(self) -> None:
        for player in list(self.active_players):
            monsters = self.field_monsters.get_monsters(player)
            for monster in monsters:
                held_item = monster.held_item.get_item()
                if held_item:
                    held_item.execute_item_action(
                        self.session, self, player, monster
                    )
                status = monster.status.get_current_status()
                if status:
                    status.execute_status_action(
                        self.session, self, monster, EffectPhase.ON_DECISION
                    )

    def apply_statuses(self) -> None:
        """
        Applies and updates status effects for all active monsters.
        """
        for monster in self.active_monsters:
            for status in monster.status.get_statuses():
                if len(self.remaining_players) > 1:
                    if status.validate_monster(self.session, monster):
                        status.set_combat_state(self)
                        status.nr_turn += 1
                        self.enqueue_action(None, status, monster)
            # avoid multiple effect status
            monster.set_stats()

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
        self._damage_map.log_damage(attacker, defender, damage, self._turn)

    def enqueue_action(
        self,
        user: Union[NPC, Monster, None],
        technique: Union[Item, Technique, Status, None],
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

    def remove_monster_from_play(self, monster: Monster) -> None:
        """
        Remove monster from play without fainting it.

        * If another monster has targeted this monster, it can change action
        * Will remove actions as well
        * currently for 'swap' technique
        """
        self.swap_tracker.clear()
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
        action_queue = self._action_queue.queue
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
        method.advance_round()
        result_tech = method.execute_tech_action(
            self.session, self, user, target
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
        status = user.status.get_current_status()
        if status:
            result_status = status.execute_status_action(
                self.session, self, user, EffectPhase.PERFORM_TECH
            )
            if result_status.extras:
                templates = [
                    T.translate(extra) for extra in result_status.extras
                ]
                template = "\n".join(templates)
                message += "\n" + template
            if result_status.statuses:
                status = random.choice(result_status.statuses)
                user.status.apply_status(self.session, status, user)

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

            self.enqueue_damage(user, target, result_tech.damage)

            if user.plague.is_infected():
                params = {"target": user.name.upper()}
                m = T.format("combat_state_plague1", params)
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
            partial(self.alert, message), action_time
        )

        is_flipped = False
        for trainer in self.ai_players:
            if user in self.field_monsters.get_monsters(trainer):
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
        result_item = item.execute_item_action(
            self.session, self, user, target
        )
        context = {
            "user": user.name,
            "name": item.name,
            "target": target.name,
        }
        message = T.format(item.use_item, context)
        # animation sprite
        item_sprite = self._method_cache.get(item, False)
        status = target.status.get_current_status()
        if result_item.success and status:
            status.execute_status_action(
                self.session, self, target, EffectPhase.PERFORM_ITEM
            )
        # handle the capture device
        if item.category == ItemCategory.capture and item_sprite:
            # retrieve tuxeball
            message += "\n" + T.translate("attempting_capture")
            action_time = result_item.num_shakes + 1.8
            self.animate_capture_monster(
                result_item.success,
                result_item.num_shakes,
                target,
                item,
                item_sprite,
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
            partial(self.alert, message), action_time
        )

    def _handle_status(self, status: Status, target: Monster) -> None:
        action_time = 0.0
        result = status.execute_status_action(
            self.session, self, target, EffectPhase.PERFORM_STATUS
        )
        status.advance_round()
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
                partial(self.alert, message), action_time
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
            self.task(animation.animation.play, interval=0.6)
            self.task(
                partial(self.sprites.add, animation, layer=50), interval=0.6
            )
            self.task(animation.kill, interval=action_time)

    def faint_monster(self, monster: Monster) -> None:
        """
        Instantly make the monster faint (will be removed later).

        Parameters:
            monster: Monster that will faint.
        """
        monster.current_hp = 0
        iid = str(monster.instance_id.hex)
        label = f"{self.name.lower()}_faint"
        set_var(self.session, label, iid)

    def award_experience_and_money(self, monster: Monster) -> None:
        """
        Award experience and money to the winners.

        Parameters:
            monster: Monster that was fainted.
        """
        reward_system = RewardSystem(self._damage_map, self.is_trainer_battle)
        rewards = reward_system.award_rewards(monster)

        # Update combat state with rewards
        self._prize += rewards.prize
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
        if winner in self.monsters_in_play_right:
            if techniques:
                tech_list = ", ".join(tech.name.upper() for tech in techniques)
                params = {"name": winner.name.upper(), "tech": tech_list}
                mex = T.format("tuxemon_new_tech", params)
                self.text_anim.add_xp_message(mex)
            owner = winner.get_owner()
            if owner.isplayer:
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
        for _, party in self.field_monsters.get_all_monsters().items():
            for monster in party:
                if monster.is_fainted:
                    params = {"name": monster.name.upper()}
                    msg = T.format("combat_fainted", params)
                    self.text_anim.add_text_animation(
                        partial(self.alert, msg), config_combat.action_time
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
        for monster_party in self.field_monsters.get_all_monsters().values():
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
            result_status = status.execute_status_action(
                self.session, self, monster, EffectPhase.CHECK_PARTY_HP
            )
            if result_status.extras:
                templates = [
                    T.translate(extra) for extra in result_status.extras
                ]
                extra = "\n".join(templates)
                action_time = self.text_anim.compute_text_anim_time(extra)
                self.text_anim.add_text_animation(
                    partial(self.alert, extra), action_time
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
        self._damage_map.remove_monster(monster)

    def initialize_hit_chances(self) -> None:
        """Initializes random hit chance values for all active monsters."""
        for monster in self.active_monsters:
            self.set_tech_hit(monster)

    def set_tech_hit(
        self, monster: Monster, value: Optional[float] = None
    ) -> None:
        """Assigns a random hit chance to the given monster."""
        if value is None:
            value = random.random()
        self._random_tech_hit[monster] = value

    def get_tech_hit(self, monster: Monster) -> float:
        """Retrieves the stored hit chance, defaulting to 0.0 if not found."""
        return self._random_tech_hit.get(monster, 0.0)

    @property
    def active_players(self) -> Iterable[NPC]:
        """All trainers still active in the battle."""
        for player in self.players:
            if not defeated(player):
                yield player

    @property
    def human_players(self) -> Iterable[NPC]:
        """Players controlled by humans."""
        for player in self.players:
            if player.isplayer:
                yield player

    @property
    def ai_players(self) -> Iterable[NPC]:
        """Players controlled by AI."""
        yield from set(self.active_players) - set(self.human_players)

    @property
    def active_monsters(self) -> Sequence[Monster]:
        """All non-fainted monsters currently in play."""
        return self.field_monsters.active_monsters

    @property
    def monsters_in_play_right(self) -> Sequence[Monster]:
        """Active monsters on the right side of the battlefield."""
        return self.field_monsters.get_monsters(self.players[0])

    @property
    def monsters_in_play_left(self) -> Sequence[Monster]:
        """Active monsters on the left side of the battlefield."""
        return self.field_monsters.get_monsters(self.players[1])

    @property
    def all_monsters_right(self) -> Sequence[Monster]:
        """All non-fainted monsters belonging to the right-side player."""
        return [m for m in self.players[0].monsters if not m.is_fainted]

    @property
    def all_monsters_left(self) -> Sequence[Monster]:
        """All non-fainted monsters belonging to the left-side player."""
        return [m for m in self.players[1].monsters if not m.is_fainted]

    @property
    def defeated_players(self) -> Sequence[NPC]:
        """All trainers who have lost (party fully fainted)."""
        return [p for p in self.players if defeated(p)]

    @property
    def remaining_players(self) -> Sequence[NPC]:
        """Alias for non-defeated players. WIP: subject to future team logic."""
        return [p for p in self.players if not defeated(p)]

    def get_bench(self, player: NPC) -> Sequence[Monster]:
        """Returns non-fainted, off-field monsters for the given player."""
        monsters_in_play = self.field_monsters.get_monsters(player)
        all_monsters = [m for m in player.monsters if not m.is_fainted]
        return [m for m in all_monsters if m not in monsters_in_play]

    def get_opponent_monsters(self, monster: Monster) -> Sequence[Monster]:
        """Returns all active enemy monsters on the opponent's field."""
        if monster in self.monsters_in_play_right:
            return self.monsters_in_play_left
        return self.monsters_in_play_right

    def get_own_monsters(self, monster: Monster) -> Sequence[Monster]:
        """Returns active allies on the same team."""
        if monster in self.monsters_in_play_right:
            return self.monsters_in_play_right
        return self.monsters_in_play_left

    def get_party(self, monster: Monster) -> Sequence[Monster]:
        """Returns all non-fainted monsters in the party that owns this monster."""
        if monster in self.monsters_in_play_right:
            return self.all_monsters_right
        return self.all_monsters_left

    def get_targets_from_map(
        self, target_type: str, user: Monster, target: Monster
    ) -> list[Monster]:
        """
        Get the targets from the target map.

        Parameters:
            target_type: The type of target (e.g. "own_monster", etc.)
            user: The Monster object that used the technique.
            target: The Monster object being targeted by the technique.
        Returns:
            A list of Monster objects.
        """
        target_map = {
            "enemy_monster": [target],
            "enemy_team": self.get_own_monsters(target),
            "enemy_trainer": self.get_party(target),
            "own_monster": [user],
            "own_team": self.get_own_monsters(user),
            "own_trainer": self.get_party(user),
        }

        return list(target_map.get(target_type, []))

    def get_targets(
        self, tech: Technique, user: Monster, target: Monster
    ) -> list[Monster]:
        """
        Get the targets.

        Parameters:
            tech: The Technique object that is being applied.
            user: The Monster object that used the technique.
            target: The Monster object being targeted by the technique.

        Returns:
            A list of Monster objects.
        """
        targets: set[Monster] = set()
        for target_type in list(TargetType):
            if tech.target[target_type]:
                targets.update(
                    self.get_targets_from_map(target_type, user, target)
                )

        if not targets:
            logger.error(f"{tech.name} has all its targets set to False")

        return list(targets)

    def clean_combat(self) -> None:
        """Clean combat."""
        for player in self.players:
            for mon in player.monsters:
                # reset status stats
                mon.set_stats()
                mon.end_combat(self.session)
                # reset type
                mon.types.reset_to_default()
                # reset technique stats
                mon.moves.set_stats()

        self._menu_visibility.reset_to_default()
        self._action_queue.clear_queue()
        self._action_queue.clear_history()
        self._action_queue.clear_pending()
        self._damage_map.clear_damage()
        self._combat_variables = {}
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
        self.client.current_music.stop()
        self.clear_combat_states()
        self.phase = None

        # open Tuxepedia if monster is captured
        if self._captured_mon and self._new_tuxepedia:
            self.client.remove_state_by_name("CombatState")
            params = {"monster": self._captured_mon, "source": self.name}
            self.client.push_state("MonsterInfoState", kwargs=params)
        else:
            self.client.push_state("FadeOutTransition", caller=self)
