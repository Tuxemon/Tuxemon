# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

from tuxemon.combat.action_queue import ActionQueue, EnqueuedAction
from tuxemon.combat.combat_context import CombatType
from tuxemon.combat.damage_tracker import DamageTracker
from tuxemon.combat.field_monsters import FieldMonsters
from tuxemon.combat.reward_system import (
    HordeRewardCalculator,
    RewardCalculator,
    TrainerRewardCalculator,
    WildRewardCalculator,
)
from tuxemon.combat.utils import battlefield
from tuxemon.db import EffectPhase, TargetType
from tuxemon.event import get_event_bus
from tuxemon.locale.locale import T
from tuxemon.technique.technique import Technique
from tuxemon.ui.combat_swap import SwapTracker

if TYPE_CHECKING:
    from tuxemon.core.core_effect import (
        ItemEffectResult,
        StatusEffectResult,
        TechEffectResult,
    )
    from tuxemon.entity.npc import NPC
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status

logger = logging.getLogger(__name__)


class CombatSession:
    def __init__(self) -> None:
        self.event_bus = get_event_bus()
        self._turn: int = 0
        self._prize: int = 0
        self._is_double: bool = False
        self._players: list[NPC] = []
        self._combat_type: CombatType | None = None
        self._random_tech_hit: dict[Monster, float] = {}
        self._combat_variables: dict[str, Any] = {}
        self.field_monsters = FieldMonsters()
        self.swap_tracker = SwapTracker()
        self.menu_visibility_map: dict[str, bool] = {}
        self.damage_tracker = DamageTracker()
        self.action_queue = ActionQueue()

    # Players management
    @property
    def players(self) -> list[NPC]:
        return self._players

    @property
    def left_player(self) -> NPC:
        return self._players[0]

    @property
    def right_player(self) -> NPC:
        return self._players[1]

    @property
    def count_players(self) -> int:
        return len(self._players)

    def set_players(self, players: list[NPC]) -> None:
        if len(players) != 2:
            raise ValueError("CombatSession requires exactly two players.")
        self._players = players

    def remove_player(self, player: NPC) -> None:
        if player not in self._players:
            return
        logger.debug(f"Remove {player.name} players")
        self._players.remove(player)

    def reset_players(self) -> None:
        logger.debug("Reset players")
        self._players.clear()

    # Player operations
    @property
    def active_players(self) -> Iterable[NPC]:
        """All trainers still active in the battle."""
        for player in self.players:
            if not player.party.is_fainted:
                yield player

    @property
    def human_players(self) -> Iterable[NPC]:
        """Players controlled by humans."""
        for player in self.players:
            if player.is_player:
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
        return self.field_monsters.get_monsters(self.left_player)

    @property
    def monsters_in_play_left(self) -> Sequence[Monster]:
        """Active monsters on the left side of the battlefield."""
        return self.field_monsters.get_monsters(self.right_player)

    @property
    def all_monsters_right(self) -> Sequence[Monster]:
        """All non-fainted monsters belonging to the right-side player."""
        return [m for m in self.left_player.monsters if not m.is_fainted]

    @property
    def all_monsters_left(self) -> Sequence[Monster]:
        """All non-fainted monsters belonging to the left-side player."""
        return [m for m in self.right_player.monsters if not m.is_fainted]

    @property
    def defeated_players(self) -> Sequence[NPC]:
        """All trainers who have lost (party fully fainted)."""
        return [p for p in self.players if p.party.is_fainted]

    @property
    def remaining_players(self) -> Sequence[NPC]:
        """Alias for non-defeated players. WIP: subject to future team logic."""
        return [p for p in self.players if not p.party.is_fainted]

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

    def get_target_monsters(
        self, targets: list[str], user: Monster, target: Monster
    ) -> list[Monster]:
        """
        Retrieves a list of monsters based on the provided targets and combat state.

        Parameters:
            targets: A list of targets to retrieve monsters for (own_monster, etc.).
            user: The monster initiating the combat.
            target: The target monster in the combat.

        Returns:
            A list of monsters matching the provided targets.

        Raises:
            ValueError: If an objective is not a valid TargetType.
        """
        monsters = []
        for objective in targets:
            if objective not in list(TargetType):
                raise ValueError(f"{objective} isn't among {list(TargetType)}")
            monsters.extend(self.get_targets_from_map(objective, user, target))
        return monsters

    # Turn management
    @property
    def turn(self) -> int:
        return self._turn

    def next_turn(self) -> int:
        self._turn += 1
        logger.debug(f"Next turn: {self._turn}")
        return self._turn

    def reset_turn(self) -> None:
        logger.debug("Turn reset to 0")
        self._turn = 0

    # Battle format
    @property
    def is_double(self) -> bool:
        return self._is_double

    def set_battle_format(self, is_double: bool) -> None:
        self._is_double = is_double
        logger.debug(
            f"Battle format set to {'Double' if is_double else 'Single'}"
        )

    # Combat Type

    @property
    def combat_type(self) -> CombatType:
        if self._combat_type is None:
            raise ValueError("Combat type has not been set.")
        return self._combat_type

    def set_combat_type(self, combat_type: CombatType) -> None:
        self._combat_type = combat_type

    def reset_combat_type(self) -> None:
        self._combat_type = None

    def get_calculator(self, combat_type: CombatType) -> RewardCalculator:
        """Return the appropriate RewardCalculator based on combat type."""
        if combat_type is CombatType.TRAINER:
            return TrainerRewardCalculator(self.damage_tracker)
        elif combat_type is CombatType.MONSTER:
            return WildRewardCalculator(self.damage_tracker)
        elif combat_type is CombatType.HORDE:
            return HordeRewardCalculator(self.damage_tracker)
        else:
            raise ValueError(f"Unknown combat type: {combat_type}")

    @property
    def is_trainer_battle(self) -> bool:
        return self.combat_type is CombatType.TRAINER

    @property
    def is_monster_battle(self) -> bool:
        return self.combat_type is CombatType.MONSTER

    @property
    def is_horde_battle(self) -> bool:
        return self.combat_type is CombatType.HORDE

    def get_start_message(self) -> str:
        """Determines and returns the appropriate alert message for combat start."""
        if self.combat_type is CombatType.TRAINER:
            params = {"name": self.right_player.name}
            return T.format("combat_trainer_appeared", params)
        elif self.combat_type is CombatType.MONSTER:
            params = {"name": self.right_player.monsters[0].name}
            return T.format("combat_wild_appeared", params)
        elif self.combat_type is CombatType.HORDE:
            horde = self.right_player.party.party_size
            return f"{T.translate('combat_horde_appeared')} ({horde})"
        else:
            raise ValueError(f"Unexpected combat_type: {self.combat_type}")

    def get_message_swap(self, character: NPC, monster: Monster) -> str:
        """Determines and returns the appropriate alert message for combat start."""
        params = {"target": monster.name}
        if self.combat_type in (CombatType.TRAINER, CombatType.MONSTER):
            params["user"] = character.name
            return T.format("combat_swap", params)
        elif self.combat_type is CombatType.HORDE:
            return T.format("combat_horde_swap", params)
        else:
            raise ValueError(f"Unexpected combat_type: {self.combat_type}")

    # Prize management
    @property
    def prize(self) -> int:
        return self._prize

    def add_prize(self, amount: int) -> None:
        self._prize += amount
        logger.debug(f"Prize increased by {amount}, total: {self._prize}")

    def reset_prize(self) -> None:
        logger.debug("Prize reset to 0")
        self._prize = 0

    # Random tech hit
    def set_tech_hit(
        self, monster: Monster, value: float | None = None
    ) -> None:
        if value is None:
            value = random.random()
        self._random_tech_hit[monster] = value
        logger.debug(f"Tech hit set for {monster}: {value}")

    def get_tech_hit(self, monster: Monster) -> float:
        value = self._random_tech_hit.get(monster, 0.0)
        logger.debug(f"Tech hit retrieved for {monster}: {value}")
        return value

    def clear_tech_hits(self) -> None:
        logger.debug("Cleared all tech hits")
        self._random_tech_hit.clear()

    # Combat variables
    def set_variable(self, key: str, value: Any) -> None:
        self._combat_variables[key] = value
        logger.debug(f"Variable set: {key} = {value}")

    def get_variable(self, key: str) -> Any | None:
        value = self._combat_variables.get(key)
        logger.debug(f"Variable retrieved: {key} = {value}")
        return value

    def clear_variables(self) -> None:
        logger.debug("Cleared all combat variables")
        self._combat_variables.clear()

    def enqueue_action(
        self,
        user: NPC | Monster | None,
        technique: Item | Technique | Status | None,
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
        self.action_queue.enqueue(action, self.turn)

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
        self.damage_tracker.log_damage(attacker, defender, damage, self.turn)

    def get_max_positions(self, player: NPC) -> int:
        """
        Calculates the maximum number of positions for a player based on
        their party size and battle mode.
        """
        if len(player.party.alive) == 1:
            return 1
        return 2 if self.is_double else 1

    def get_available_positions(self, player: NPC) -> int:
        """
        Returns the number of available positions for a player on the battlefield.
        """
        max_positions = self.get_max_positions(player)
        on_the_field = len(self.field_monsters.get_monsters(player))
        return max_positions - on_the_field

    def update_tuxepedia(self, player: NPC, monster: Monster) -> None:
        """
        Updates the tuxepedia for human players when a monster is encountered.

        Parameters:
            player: The player who encountered the monster.
            monster: The monster that was encountered.
        """
        for other_player in self.players:
            if other_player.is_player and other_player != player:
                var = self.get_variable(monster.slug)
                if var is None:
                    other_player.tuxepedia.register_seen(monster.slug)
                    self.set_variable(monster.slug, True)

    def initialize_hit_chances(self) -> None:
        """Initializes random hit chance values for all active monsters."""
        for monster in self.active_monsters:
            self.set_tech_hit(monster)

    def check_decisions(self, session: Session) -> None:
        for player in list(self.active_players):
            monsters = self.field_monsters.get_monsters(player)
            for monster in monsters:
                held_item = monster.held_item
                if held_item:
                    held_item.use(session, player, monster)
                status = monster.status.current_status
                if status:
                    status.use(session, EffectPhase.ON_DECISION)

    def apply_statuses(self, session: Session) -> None:
        """
        Applies and updates status effects for all active monsters.
        """
        for monster in self.active_monsters:
            for status in monster.status.get_statuses():
                if len(self.remaining_players) > 1:
                    if status.validate_monster(session, monster):
                        status.tick_turn()
                        self.enqueue_action(None, status, monster)

    def track_enemy_monsters(self, session: Session) -> None:
        """
        Records properties of enemy monsters that participated in battle.
        """
        for player in self.remaining_players:
            monsters = self.field_monsters.get_monsters(player)
            if monsters and not player.is_player:
                for mon in monsters:
                    battlefield(session, mon)

    def fill_battlefield_positions(self, ask: bool = False) -> None:
        """
        Emits events for each player who needs to fill battlefield positions.

        Parameters:
            ask: If True, human players will be prompted to choose a monster.
        """
        for player in self.active_players:
            max_positions = self.get_max_positions(player)

            # Handle sprite positioning for double battles
            if max_positions == 1 and self.is_double:
                on_the_field = self.field_monsters.get_monsters(player)
                if on_the_field:
                    monster = on_the_field[0]
                    self.event_bus.publish(
                        "update_sprite_position",
                        player=player,
                        monster=monster,
                    )

            positions_available = self.get_available_positions(player)
            if positions_available:
                self.event_bus.publish(
                    "monster_needed", player=player, ask=ask
                )

            on_the_field = self.field_monsters.get_monsters(player)
            for monster in on_the_field:
                self.update_tuxepedia(player, monster)

    def add_monster_into_play(
        self,
        session: Session,
        player: NPC,
        monster: Monster,
        removed: Monster | None = None,
    ) -> None:
        self.field_monsters.add_monster(player, monster)

        for mon in self.active_monsters:
            mon.status.remove_bonded_statuses(session)

        phase = EffectPhase.SWAP_MONSTER

        entry_status = monster.status.current_status
        if entry_status:
            entry_status.use(session, phase)

        if removed:
            exit_status = removed.status.current_status
            if exit_status:
                exit_status.use(session, phase)

        self.event_bus.publish(
            "monster_added", player=player, monster=monster, removed=removed
        )

    def pre_checking(
        self,
        session: Session,
        monster: Monster,
        technique: Technique,
        target: Monster,
    ) -> Technique:
        """
        Pre checking allows to check if there are statuses
        or other conditions that change the chosen technique.
        """
        logger.debug(f"[PreCheck Start] {monster.name} using {technique.slug}")
        status = monster.status.current_status
        if status:
            result_status = status.use(session, EffectPhase.PRE_CHECKING)
            if result_status.techniques:
                technique = random.choice(result_status.techniques)

        if monster.plague.is_infected() and any(
            technique.target.get(target_type, False)
            for target_type in ["enemy_monster", "enemy_team", "enemy_trainer"]
        ):
            slug = monster.plague.get_most_severe_plague_slug()
            if slug:
                alt_technique = Technique.create(slug)
                result = alt_technique.use(session, monster, target)
                if result.success:
                    logger.debug(
                        f"[Plague Override] {monster.name} switches to {alt_technique.slug}"
                    )
                    technique = alt_technique
        logger.debug(f"[PreCheck End] {monster.name} using {technique.slug}")
        return technique

    def apply_technique(
        self, session: Session, tech: Technique, user: Monster, target: Monster
    ) -> tuple[TechEffectResult, StatusEffectResult | None]:
        result = tech.use(session, user, target)
        logger.debug(
            f"{user.name} used {tech.slug} on {target.name} > success={result.success}"
        )

        status_result = None
        status = user.status.current_status
        if status:
            status_result = status.use(session, EffectPhase.PERFORM_TECH)
            if status_result.statuses:
                chosen = random.choice(status_result.statuses)
                user.status.apply_status(session, chosen)
                get_event_bus().publish("status_applied")

        return result, status_result

    def apply_item(
        self,
        session: Session,
        item: Item,
        user: NPC,
        target: Monster | None,
    ) -> ItemEffectResult:
        result = item.use(session, user, target)
        logger.debug(
            f"{user.name} used {item.slug} on {target.name if target else 'None'} > success={result.success}"
        )

        if target:
            status = target.status.current_status
            if result.success and status:
                status.use(session, EffectPhase.PERFORM_ITEM)
        return result

    def apply_status(
        self,
        session: Session,
        status: Status,
        target: Monster,
        phase: EffectPhase,
    ) -> StatusEffectResult:
        result = status.use(session, phase)
        logger.debug(
            f"{status.slug} applied to {target.name} during {phase.name}"
        )
        return result

    def reset(self) -> None:
        logger.debug("Resetting CombatSession")
        self.reset_turn()
        self.reset_prize()
        self.clear_tech_hits()
        self.clear_variables()
        self.reset_players()
        self.set_battle_format(False)
        self.reset_combat_type()
        self.menu_visibility_map.clear()
        self.damage_tracker.clear_damage()
        self.action_queue.clear_queue()
        self.action_queue.clear_history()
        self.action_queue.clear_pending()
        self.field_monsters.clear_all()
        self.swap_tracker.clear()
