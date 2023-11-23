# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections import defaultdict
from collections.abc import Iterable, MutableMapping, Sequence
from functools import partial
from itertools import chain
from typing import Literal, NamedTuple, Optional, Union

import pygame
from pygame.rect import Rect

from tuxemon import graphics, state, tools
from tuxemon.animation import Animation, Task
from tuxemon.combat import alive_party, defeated, get_awake_monsters
from tuxemon.db import BattleGraphicsModel, ItemCategory, SeenStatus
from tuxemon.item.item import Item
from tuxemon.locale import T
from tuxemon.monster import Monster
from tuxemon.npc import NPC
from tuxemon.platform.const import buttons
from tuxemon.platform.events import PlayerInput
from tuxemon.sprite import Sprite
from tuxemon.states.monster_info import MonsterInfoState
from tuxemon.states.transition.fade import FadeOutTransition
from tuxemon.surfanim import SurfaceAnimation
from tuxemon.technique.technique import Technique
from tuxemon.tools import assert_never
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea

from .park_animations import ParkAnimations

logger = logging.getLogger(__name__)

ParkPhase = Literal[
    "begin",
    "ready",
    "housekeeping phase",
    "decision phase",
    "pre action phase",
    "action phase",
    "post action phase",
    "resolve match",
    "ran away",
    "end combat",
]


class EnqueuedAction(NamedTuple):
    user: Union[Monster, NPC, None]
    method: Union[Technique, Item, None]
    target: Monster


# This is the time, in seconds, that the text takes to display.
LETTER_TIME: float = 0.02
# This is the time, in seconds, that the animation takes to finish.
ACTION_TIME: float = 2.0


def compute_text_animation_time(message: str) -> float:
    """
    Compute required time for a text animation.

    Parameters:
        message: The given text to be animated.

    Returns:
        The time in seconds expected to be taken by the animation.
    """
    return ACTION_TIME + LETTER_TIME * len(message)


class MethodAnimationCache:
    def __init__(self) -> None:
        self._sprites: dict[Union[Technique, Item], Optional[Sprite]] = {}

    def get(
        self, method: Union[Technique, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return a sprite usable as a method animation.

        Parameters:
            method: Technique whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the method animation.

        """
        try:
            return self._sprites[method]
        except KeyError:
            sprite = self.load_method_animation(method, is_flipped)
            self._sprites[method] = sprite
            return sprite

    @staticmethod
    def load_method_animation(
        method: Union[Technique, Item], is_flipped: bool
    ) -> Optional[Sprite]:
        """
        Return animated sprite from a method.

        Parameters:
            method: Method whose sprite is requested.
            is_flipped: Flag to determine whether animation frames should be flipped.

        Returns:
            Sprite associated with the method animation.

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


class ParkState(ParkAnimations):
    """The state-menu responsible for all combat related tasks and functions.
        .. image:: images/combat/monster_drawing01.png

    General description of this class:
        * implements a simple state machine
        * various phases are executed using a queue of actions
        * "decision queue" is used to queue player interactions/menus
        * this class holds mostly logic, though some graphical functions exist
        * most graphical functions are contained in "ParkAnimations" class

    """

    draw_borders = False
    escape_key_exits = False

    def __init__(
        self,
        players: tuple[NPC, NPC],
        graphics: BattleGraphicsModel,
    ) -> None:
        self.phase: Optional[ParkPhase] = None
        self._damage_map: MutableMapping[Monster, set[Monster]] = defaultdict(
            set
        )
        self._method_cache = MethodAnimationCache()
        self._decision_queue: list[Monster] = []
        self._action_queue: list[EnqueuedAction] = []
        self._log_action: list[tuple[int, EnqueuedAction]] = []
        self._monster_sprite_map: MutableMapping[Monster, Sprite] = {}
        self._layout = dict()  # player => home areas on screen
        self._turn: int = 0
        self._captured: bool = False
        self._captured_mon: Optional[Monster] = None
        self._new_tuxepedia: bool = False
        self._run: bool = False
        self._post_animation_task: Optional[Task] = None
        self._xp_message = None
        self._doll_modifier: float = 1.0
        self._food_modifier: float = 1.0
        self._distance: float = 0.5

        super().__init__(players, graphics)
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

    def draw_hp_bars(self) -> None:
        """Go through the HP bars and redraw them."""
        for monster, hud in self.hud.items():
            rect = Rect(0, 0, tools.scale(70), tools.scale(8))
            rect.right = hud.image.get_width() - tools.scale(8)
            if hud.player:
                rect.top += tools.scale(18)
            else:
                rect.top += tools.scale(12)
                self._hp_bars[monster].draw(hud.image, rect)

    def determine_phase(
        self,
        phase: Optional[ParkPhase],
    ) -> Optional[ParkPhase]:
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

            if remaining == 1:
                return "ran away"
            else:
                return "housekeeping phase"

        elif phase == "ran away":
            return "end combat"

        elif phase == "end combat":
            return None

        else:
            assert_never(phase)

    def transition_phase(self, phase: ParkPhase) -> None:
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
        if phase == "begin" or phase == "ready" or phase == "pre action phase":
            pass

        elif phase == "housekeeping phase":
            self._turn += 1
            # fill all battlefield positions, but on round 1, don't ask
            self.fill_battlefield_positions(ask=self._turn > 1)

            # record the useful properties of the last monster we fought
            monster_record = self.monsters_in_play_ai[0]
            if monster_record in self.active_monsters:
                var = self.players[0].game_variables
                var["park_last_monster_name"] = monster_record.name
                var["park_last_monster_level"] = monster_record.level
                var["park_last_monster_type"] = monster_record.types[0].slug
                var["park_last_monster_category"] = monster_record.category
                var["park_last_monster_shape"] = monster_record.shape
                # Avoid reset string to seen if monster has already been caught
                if monster_record.slug not in self.players[0].tuxepedia:
                    self.players[0].tuxepedia[
                        monster_record.slug
                    ] = SeenStatus.seen

        elif phase == "decision phase":
            # saves random value, so we are able to reproduce
            # inside the condition files if a tech hit or missed
            if not self._decision_queue:
                for player in self.human_players:
                    # tracks human players who need to choose an action
                    self._decision_queue.extend(self.monsters_in_play[player])
                technique = Technique()
                target = self.monsters_in_play_human[0]
                for trainer in self.ai_players:
                    for monster in self.monsters_in_play[trainer]:
                        if self._distance > random.random():
                            technique.load("menu_run")
                            self.enqueue_action(monster, technique, target)
                        else:
                            technique.load("park")
                            self.enqueue_action(monster, technique, target)

        elif phase == "action phase":
            self.sort_action_queue()

        elif phase == "post action phase":
            pass

        elif phase == "resolve match":
            pass

        elif phase == "ran away":
            self.task(
                partial(self.client.push_state, WaitForInputState()),
                ACTION_TIME,
            )

        elif phase == "end combat":
            self.end_combat()

        else:
            assert_never(phase)

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
            primary_order = sort_order.index(sort)

            if sort == "utility":
                return primary_order, 0
            elif sort == "meta":
                return primary_order, 1
            else:
                return primary_order, 2

        sort_order = [
            "utility",
            "meta",
            "item",
        ]

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

    def fill_battlefield_positions(self, ask: bool = False) -> None:
        """
        Check the battlefield for unfilled positions and send out monsters.

        Parameters:
            ask: If True, then open dialog for human players.

        """
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
                    self.add_monster_into_play(player, next(available))

    def add_monster_into_play(
        self,
        player: NPC,
        monster: Monster,
    ) -> None:
        """
        Add a monster to the battleground.

        Parameters:
            player: Player who adds the monster, if any.
            monster: Added monster.

        """
        item = Item()
        item.load(monster.capture_device)
        self.animate_monster_release(player, monster)
        self.monsters_in_play[player].append(monster)
        if monster in self.players[1].monsters:
            message = T.format(
                "combat_wild_appeared",
                {"name": monster.name.upper()},
            )
            self.text_animations_queue.append(
                (partial(self.alert, message), 0)
            )
        self.build_hud(
            self._layout[player]["hud"][0],
            self.monsters_in_play[player][0],
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
        from tuxemon.states.park.park_menus import MainParkMenuState

        assert monster.owner
        message = T.format(
            "combat_player_choice", {"name": monster.owner.name.upper()}
        )
        self.text_animations_queue.append((partial(self.alert, message), 0))
        rect_screen = self.client.screen.get_rect()
        rect = Rect(0, 0, rect_screen.w // 2.5, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h

        state = self.client.push_state(
            MainParkMenuState(
                cmb=self,
                monster=monster,
            )
        )
        state.rect = rect

    def enqueue_action(
        self,
        user: Union[NPC, Monster, None],
        method: Union[Item, Technique, None],
        target: Monster,
    ) -> None:
        """
        Add some method to the action queue.

        Parameters:
            user: The user of the method.
            method: The method used.
            target: The target of the action.

        """
        action = EnqueuedAction(user, method, target)
        self._action_queue.append(action)
        self._log_action.append((self._turn, action))

    def perform_action(
        self,
        user: Union[Monster, NPC, None],
        method: Union[Technique, Item, None],
        target: Monster,
    ) -> None:
        """
        Perform the action.

        Parameters:
            user: Monster that does the action.
            method: Technique or item used.
            target: Monster that receives the action.

        """
        action_time = 0.0
        # monster uses move
        if isinstance(method, Technique) and isinstance(user, Monster):
            method.advance_round()
            context = {
                "user": user.name,
                "name": method.name,
                "target": target.name,
            }
            message: str = ""
            # attempt failed of capture
            if self._captured_mon and not self._captured:
                if self._captured_mon == user:
                    message += "\n" + T.translate("captured_failed")
                    self._captured_mon = None
                    action_time += compute_text_animation_time(message)
            message += "\n" + T.format(method.use_tech, context)
            self.text_animations_queue.append(
                (partial(self.alert, message), action_time)
            )
            if method.slug == "menu_run":
                for remove in self.players:
                    self.clean_combat()
                    del self.monsters_in_play[remove]
                    self.players.remove(remove)

        # player uses item
        if isinstance(method, Item) and isinstance(user, NPC):
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
                    self,
                )
            else:
                self.animate_throw_item(target, method)
                # extra output
                if result_item["extra"]:
                    tmpl = T.translate(result_item["extra"])
                    message += "\n" + tmpl
                    action_time += compute_text_animation_time(message)
                # item animation
                target_sprite = self._monster_sprite_map.get(target, None)
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
        """
        Generator of human players.

        Returns:
            Iterable with human players.

        """
        for player in self.players:
            if player.isplayer:
                yield player

    @property
    def ai_players(self) -> Iterable[NPC]:
        """
        Generator of ai players.

        Returns:
            Iterable with ai players.

        """
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
    def monsters_in_play_human(self) -> Sequence[Monster]:
        """
        List of any monsters in battle (human).

        Returns:
            Sequence of active monsters in play (human).

        """
        return self.monsters_in_play[self.players[0]]

    @property
    def monsters_in_play_ai(self) -> Sequence[Monster]:
        """
        List of any monsters in battle (ai).

        Returns:
            Sequence of active monsters in play (ai).

        """
        return self.monsters_in_play[self.players[1]]

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
        return [p for p in self.players if not defeated(p)]

    def clean_combat(self) -> None:
        """Clean combat."""
        self._action_queue = list()
        self._log_action = list()

    def end_combat(self) -> None:
        """End the combat."""
        self._food_modifier = 1.0
        self._doll_modifier = 1.0
        self._distance = 0.5
        self.clean_combat()

        # fade music out
        self.client.event_engine.execute_action("fadeout_music", [1000])

        # remove any menus that may be on top of the combat state
        while self.client.current_state is not self:
            self.client.pop_state()

        # open Tuxepedia if monster is captured
        if self._captured and self._captured_mon and self._new_tuxepedia:
            self.client.pop_state()
            self.client.push_state(
                MonsterInfoState(monster=self._captured_mon)
            )
        else:
            self.phase = None
            self.client.push_state(FadeOutTransition(caller=self))
