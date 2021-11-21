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
# states.combat Combat Start module
#
#
from __future__ import annotations
import logging
from collections import defaultdict, namedtuple
from functools import partial
from itertools import chain

from pygame.rect import Rect
from tuxemon import audio, state, tools, graphics
from tuxemon.combat import check_status, fainted, get_awake_monsters, defeated
from tuxemon.locale import T
from tuxemon.platform.const import buttons
from tuxemon.surfanim import SurfaceAnimation
from tuxemon.session import local_session
from tuxemon.sprite import Sprite
from tuxemon.technique import Technique
from tuxemon.ui.draw import GraphicBox
from tuxemon.ui.text import TextArea
from .combat_animations import CombatAnimations
from typing import Dict, Optional, Any, Literal, Tuple, Union, TYPE_CHECKING,\
    Sequence, Iterable, Mapping, List, MutableMapping, AbstractSet, NamedTuple,\
    overload, Set
from tuxemon.platform.events import PlayerInput
import pygame
from tuxemon.tools import assert_never
from tuxemon.monster import Monster
from tuxemon.menu.interface import MenuItem, ExpBar, HpBar
from tuxemon.animation import Task
from tuxemon.item.item import Item
from tuxemon.states.monster import MonsterMenuState
from tuxemon.states.transition.fade import FadeOutTransition

if TYPE_CHECKING:
    from tuxemon.player import Player
    from tuxemon.npc import NPC

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
    user: Union[NPC, Monster, None]
    technique: Union[Technique, Item]
    target: Monster


# TODO: move to mod config
MULT_MAP = {
    4: "attack_very_effective",
    2: "attack_effective",
    0.5: "attack_resisted",
    0.25: "attack_weak",
}


class TechniqueAnimationCache:
    def __init__(self) -> None:
        self._sprites: Dict[Technique, Optional[Sprite]] = {}

    def get(self, technique: Technique) -> Optional[Sprite]:
        """
        Return a sprite usable as a technique animation.

        Parameters:
            technique: Technique whose sprite is requested.

        Returns:
            Sprite associated with the technique animation.

        """
        try:
            return self._sprites[technique]
        except KeyError:
            sprite = self.load_technique_animation(technique)
            self._sprites[technique] = sprite
            return sprite

    @staticmethod
    def load_technique_animation(technique: Technique) -> Optional[Sprite]:
        """
        Return animated sprite from a technique.

        Parameters:
            technique: Technique whose sprite is requested.

        Returns:
            Sprite associated with the technique animation.

        """
        if not technique.images:
            return None
        frame_time = 0.09
        images = list()
        for fn in technique.images:
            image = graphics.load_and_scale(fn)
            images.append((image, frame_time))
        tech = SurfaceAnimation(images, False)
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

    def startup(
        self,
        combat_type: Optional[Literal["monster", "trainer"]] = None,
        **kwargs: Any,
    ) -> None:
        self.max_positions = 1  # TODO: make dependant on match type
        self.phase = None
        self.monsters_in_play: MutableMapping[NPC, List[Monster]] = defaultdict(list)
        self._damage_map: MutableMapping[Monster, Set[Monster]] = defaultdict(set)  # track damage so experience can be awarded later
        self._technique_cache = TechniqueAnimationCache()
        self._decision_queue: List[Monster] = []  # queue for monsters that need decisions
        self._action_queue: List[EnqueuedAction] = []  # queue for techniques, items, and status effects
        self._status_icons: List[Sprite] = []  # list of sprites that are status icons
        self._monster_sprite_map: MutableMapping[Monster, Sprite] = {}
        self._layout = dict()  # player => home areas on screen
        self._animation_in_progress = False  # if true, delay phase change
        self._round = 0

        super().startup(**kwargs)
        self.is_trainer_battle = combat_type == "trainer"
        self.players = list(self.players)
        self.show_combat_dialog()
        self.transition_phase("begin")
        self.task(partial(setattr, self, "phase", "ready"), 3)

    def update(self, time_delta: float) -> None:
        """
        Update the combat state.  State machine is checked.

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
        for monster, hud in self.hud.items():
            rect = Rect(0, 0, tools.scale(70), tools.scale(8))
            rect.right = hud.image.get_width() - tools.scale(8)
            rect.top += tools.scale(12)
            self._hp_bars[monster].draw(hud.image, rect)

    def draw_exp_bars(self) -> None:
        """Go through the EXP bars and redraw them."""
        for monster, hud in self.hud.items():
            if hud.player:
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
                positions_available = (
                    self.max_positions - len(self.monsters_in_play[player])
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
        if phase == "begin" or phase == "ready" or phase == "pre action phase":
            pass

        elif phase == "housekeeping phase":
            self._round += 1
            # fill all battlefield positions, but on round 1, don't ask
            self.fill_battlefield_positions(ask=self._round > 1)

            # record the useful properties of the last monster we fought
            monster_record = self.monsters_in_play[self.players[1]][0]
            if monster_record in self.active_monsters:
                self.players[0].game_variables["battle_last_monster_name"] = monster_record.name
                self.players[0].game_variables["battle_last_monster_level"] = monster_record.level
                self.players[0].game_variables["battle_last_monster_type"] = monster_record.slug
                self.players[0].game_variables["battle_last_monster_category"] = monster_record.category
                self.players[0].game_variables["battle_last_monster_shape"] = monster_record.shape

        elif phase == "decision phase":
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
            self.players[0].game_variables["battle_last_result"] = "ran"
            self.alert(T.translate("combat_player_run"))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            # if you run in PvP, you need "defeated message"
            self.task(partial(self.client.push_state, WaitForInputState), 2)
            self.suppress_phase_change(3)

        elif phase == "draw match":
            self.players[0].set_party_status()
            self.players[0].game_variables["battle_last_result"] = "draw"

            # it is a draw match; both players were defeated in same round
            self.alert(T.translate("combat_draw"))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            self.task(partial(self.client.push_state, WaitForInputState), 2)
            self.suppress_phase_change(3)

        elif phase == "has winner":
            # TODO: proper match check, etc
            # This assumes that player[0] is the human playing in single player
            self.players[0].set_party_status()
            if self.remaining_players[0] == self.players[0]:
                self.players[0].game_variables["battle_last_result"] = "won"
                self.alert(T.translate("combat_victory"))
            else:
                self.players[0].game_variables["battle_last_result"] = "lost"
                self.players[0].game_variables["battle_lost_faint"] = "true"
                self.alert(T.translate("combat_defeat"))

            # after 3 seconds, push a state that blocks until enter is pressed
            # after the state is popped, the combat state will clean up and close
            self.task(partial(self.client.push_state, WaitForInputState), 2)
            self.suppress_phase_change(3)

        elif phase == "end combat":
            self.players[0].set_party_status()
            self.end_combat()

        else:
            assert_never(phase)

    def get_combat_decision_from_ai(self, monster: Monster) -> EnqueuedAction:
        """
        Get ai action from a monster and enqueue it.

        Parameters:
            monster: Monster whose action will be decided.

        Returns:
            Enqueued action of the monster.

        """
        # TODO: parties/teams/etc to choose opponents
        opponents = self.monsters_in_play[self.players[0]]
        technique, target = monster.ai.make_decision(monster, opponents)
        return EnqueuedAction(monster, technique, target)

    def sort_action_queue(self) -> None:
        """Sort actions in the queue according to game rules

        * Swap actions are always first
        * Techniques that damage are sorted by monster speed
        * Items are sorted by trainer speed

        """

        def rank_action(action: EnqueuedAction) -> Tuple[int, int]:
            sort = action.technique.sort
            primary_order = sort_order.index(sort)

            if sort == "meta":
                # all meta items sorted together
                # use of 0 leads to undefined sort/probably random
                return primary_order, 0

            else:
                # TODO: determine the secondary sort element,
                # monster speed, trainer speed, etc
                assert action.user
                return primary_order, action.user.speed_test(action)

        # TODO: move to mod config
        sort_order = [
            "meta",
            "item",
            "utility",
            "potion",
            "food",
            "heal",
            "damage",
        ]

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

    def ask_player_for_monster(self, player: NPC) -> None:
        """
        Open dialog to allow player to choose a Tuxemon to enter into play.

        Parameters:
            player: Player who has to select a Tuxemon.

        """

        def add(menuitem: MenuItem[Monster]) -> None:
            monster = menuitem.game_object
            if monster.current_hp == 0:
                tools.open_dialog(
                    local_session,
                    [
                        T.format(
                            "combat_fainted",
                            parameters={"name": monster.name},
                        ),
                    ],
                )
            elif monster in self.active_monsters:
                tools.open_dialog(
                    local_session,
                    [
                        T.format(
                            "combat_isactive",
                            parameters={"name": monster.name},
                        ),
                    ],
                )
                msg = T.translate("combat_replacement_is_fainted")
                tools.open_dialog(local_session, [msg])
            else:
                self.add_monster_into_play(player, monster)
                self.client.pop_state()

        state = self.client.push_state(MonsterMenuState)
        # must use a partial because alert relies on a text box that may not
        # exist until after the state hs been startup
        state.task(partial(state.alert, T.translate("combat_replacement")), 0)
        state.on_menu_selection = add
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
        released = False
        for player in self.active_players:
            positions_available = (
                self.max_positions - len(self.monsters_in_play[player])
            )
            if positions_available:
                available = get_awake_monsters(player)
                for _ in range(positions_available):
                    released = True
                    if player in humans and ask:
                        self.ask_player_for_monster(player)
                    else:
                        self.add_monster_into_play(player, next(available))

        if released:
            self.suppress_phase_change()

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
        # TODO: refactor some into the combat animations
        self.animate_monster_release(player, monster)
        self.build_hud(self._layout[player]["hud"][0], monster)
        self.monsters_in_play[player].append(monster)

        # TODO: not hardcode
        if player is self.players[0]:
            self.alert(
                T.format(
                    "combat_call_tuxemon",
                    {"name": monster.name.upper()},
                ),
            )
        elif self.is_trainer_battle:
            self.alert(
                T.format(
                    "combat_opponent_call_tuxemon",
                    {
                        "name": monster.name.upper(),
                        "user": player.name.upper(),
                    },
                )
            )
        else:
            self.alert(
                T.format(
                    "combat_wild_appeared",
                    {"name": monster.name.upper()},
                ),
            )

    def reset_status_icons(self) -> None:
        """
        Update/reset status icons for monsters.

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
                    self.load_sprite(
                        status.icon,
                        layer=200,
                        center=rect.topleft,
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
        from tuxemon.states.combat.combat_menus import MainCombatMenuState

        message = T.format("combat_monster_choice", {"name": monster.name})
        self.alert(message)
        rect_screen = self.client.screen.get_rect()
        rect = Rect(0, 0, rect_screen.w // 2.5, rect_screen.h // 4)
        rect.bottomright = rect_screen.w, rect_screen.h

        state = self.client.push_state(
            MainCombatMenuState,
            monster=monster,
            columns=2,
        )
        state.rect = rect

    def skip_phase_change(self) -> None:
        """
        Skip phase change animations.

        Useful if player wants to skip a battle animation.
        """
        for ani in self.animations:
            ani.finish()

    def enqueue_action(
        self,
        user: Union[NPC, Monster, None],
        technique: Technique,
        target: Monster,
    ) -> None:
        """
        Add some technique or status to the action queue.

        Parameters:
            user: The user of the technique.
            technique: The technique used.
            target: The target of the action.

        """
        self._action_queue.append(EnqueuedAction(user, technique, target))

    def rewrite_action_queue_target(
        self,
        original: Monster,
        new: Monster,
    ) -> None:
        """
        Used for swapping monsters.

        Parameters:
            original: Original targeted monster.
            new: New monster.

        """
        # rewrite actions in the queue to target the new monster
        for index, action in enumerate(self._action_queue):
            if action.target is original:
                new_action = EnqueuedAction(action.user, action.technique, new)
                self._action_queue[index] = new_action

    def remove_monster_from_play(
        self,
        trainer: Monster,
        monster: Monster,
    ) -> None:
        """
        Remove monster from play without fainting it.

        * If another monster has targeted this monster, it can change action
        * Will remove actions as well
        * currently for 'swap' technique

        :param monster:
        :return:
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

    def suppress_phase_change(
        self,
        delay: float = 3.0,
    ) -> Optional[Task]:
        """
        Prevent the combat phase from changing for a limited time.

        Use this function to prevent the phase from changing.  When
        animating elements of the phase, call this to prevent player
        input as well as phase changes.

        Parameters:
            delay: Amount of seconds to delay phase changes.

        """
        if self._animation_in_progress:
            logger.debug("double suppress: bug?")
            return None

        self._animation_in_progress = True
        return self.task(
            partial(setattr, self, "_animation_in_progress", False),
            delay,
        )

    @overload
    def perform_action(
        self,
        user: Optional[Monster],
        technique: Technique,
        target: Monster,
    ) -> None:
        pass

    @overload
    def perform_action(
        self,
        user: Optional[NPC],
        technique: Item,
        target: Monster,
    ) -> None:
        pass

    def perform_action(
        self,
        user: Union[Monster, NPC, None],
        technique: Union[Technique, Item],
        target: Monster,
    ) -> None:
        """
        Perform the action.

        Parameters:
            user: Monster that does the action.
            technique: Technique or item used.
            target: Monster that receives the action.

        """
        technique.advance_round()

        # This is the time, in seconds, that the animation takes to finish.
        action_time = 3.0

        result = technique.use(user, target)

        if technique.use_item:
            # "Monster used move!"
            context = {
                "user": getattr(user, "name", ""),
                "name": technique.name,
                "target": target.name,
            }
            message = T.format(technique.use_item, context)
        else:
            message = ""

        # TODO: caching sounds
        audio.load_sound(technique.sfx).play()

        # action is performed, so now use sprites to animate it
        # this value will be None if the target is off screen
        target_sprite = self._monster_sprite_map.get(target, None)

        # slightly delay the monster shake, so technique animation
        # is synchronized with the damage shake motion
        hit_delay = 0.0
        if user:

            # TODO: a real check or some params to test if should tackle, etc
            if result["should_tackle"]:
                hit_delay += 0.5
                user_sprite = self._monster_sprite_map[user]
                self.animate_sprite_tackle(user_sprite)

                if target_sprite:
                    self.task(partial(self.animate_sprite_take_damage, target_sprite), hit_delay + 0.2)
                    self.task(partial(self.blink, target_sprite), hit_delay + 0.6)

                # TODO: track total damage
                # Track damage
                self._damage_map[target].add(user)

                element_damage_key = MULT_MAP.get(result["element_multiplier"])
                if element_damage_key:
                    m = T.translate(element_damage_key)
                    message += "\n" + m

                for status in result.get("statuses", []):
                    m = T.format(
                        status.use_item,
                        {
                            "name": technique.name,
                            "user": status.link.name if status.link else "",
                            "target": status.carrier.name,
                        },
                    )
                    message += "\n" + m

            else:  # assume this was an item used

                # handle the capture device
                if result["capture"]:
                    message += "\n" + T.translate("attempting_capture")
                    action_time = result["num_shakes"] + 1.8
                    self.animate_capture_monster(
                        result["success"], result["num_shakes"],
                        target,
                    )

                    # TODO: Don't end combat right away; only works with SP,
                    # and 1 member parties end combat right here
                    if result["success"]:
                        self.task(self.end_combat, action_time + 0.5)  # Display 'Gotcha!' first.
                        self.task(partial(self.alert, T.translate("gotcha")), action_time)
                        self._animation_in_progress = True
                        return

                # generic handling of anything else
                else:
                    msg_type = (
                        "use_success" if result["success"] else "use_failure"
                    )
                    template = getattr(technique, msg_type)
                    if template:
                        message += "\n" + T.translate(template)

            self.alert(message)
            self.suppress_phase_change(action_time)

        else:
            if result["success"]:
                self.suppress_phase_change()
                self.alert(T.format(
                    "combat_status_damage",
                    {"name": target.name, "status": technique.name},
                ))

        tech_sprite = self._technique_cache.get(technique)
        if result["success"] and target_sprite and tech_sprite:
            tech_sprite.rect.center = target_sprite.rect.center
            self.task(tech_sprite.animation.play, hit_delay)
            self.task(
                partial(self.sprites.add, tech_sprite, layer=50),
                hit_delay,
            )
            self.task(tech_sprite.kill, 3)

    def faint_monster(self, monster: Monster) -> None:
        """
        Instantly make the monster faint (will be removed later).

        Parameters:
            monster: Monster that will faint.

        """
        faint = Technique("status_faint")
        monster.current_hp = 0
        monster.status = [faint]

        """
        Experience is earned when the target monster is fainted.
        Any monsters who contributed any amount of damage will be awarded
        Experience is distributed evenly to all participants
        """
        if monster in self._damage_map:
            # Award Experience
            awarded_exp = (
                monster.total_experience // (
                    monster.level * len(self._damage_map[monster])
                )
            )
            for winners in self._damage_map[monster]:
                winners.give_experience(awarded_exp)

            # Remove monster from damage map
            del self._damage_map[monster]

    def animate_party_status(self) -> None:
        """
        Animate monsters that need to be fainted.

        * Animation to remove monster is handled here
        TODO: check for faint status, not HP

        """
        for _, party in self.monsters_in_play.items():
            for monster in party:
                if fainted(monster):
                    self.alert(
                        T.format(
                            "combat_fainted",
                            {"name": monster.name},
                        ),
                    )
                    self.animate_monster_faint(monster)
                    self.suppress_phase_change(3)

    def check_party_hp(self) -> None:
        """
        Apply status effects, then check HP, and party status.

        * Monsters will be removed from play here

        """
        for _, party in self.monsters_in_play.items():
            for monster in party:
                self.animate_hp(monster)
                if (
                    monster.current_hp <= 0
                    and not check_status(monster, "status_faint")
                ):
                    self.remove_monster_actions_from_queue(monster)
                    self.faint_monster(monster)

                    # If a monster fainted, exp was given, thus the exp bar
                    # should be updated
                    # The exp bar must only be animated for the player's
                    # monsters
                    # Enemies don't have a bar, doing it for them will
                    # cause a crash
                    for monster in self.monsters_in_play[local_session.player]:
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

    def trigger_player_run(self, player: NPC) -> None:
        """
        WIP.  make player run from battle.

        This is a temporary fix for now. Expected to be called by the
        command menu.

        Parameters:
            player: The player leaving combat.

        """
        # TODO: non SP things
        del self.monsters_in_play[player]
        self.players.remove(player)

    def end_combat(self) -> None:
        """End the combat."""
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

        self.client.push_state(FadeOutTransition, caller=self)
