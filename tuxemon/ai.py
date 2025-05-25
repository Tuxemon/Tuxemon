# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml

from tuxemon import prepare
from tuxemon.combat import has_status, pre_checking, recharging
from tuxemon.constants import paths
from tuxemon.formula import simple_damage_multiplier
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


@dataclass
class ItemEntry:
    hp_below: Optional[float] = None
    hp_above: Optional[float] = None
    hp_range: Optional[tuple[float, float]] = None
    status_effects: Optional[list[str]] = None
    monster_slugs: Optional[list[str]] = None


@dataclass
class AIItems:
    items: dict[str, ItemEntry]


@dataclass
class UserMonsterEntry:
    health_weight: Optional[float] = None
    armour_weight: Optional[float] = None
    dodge_weight: Optional[float] = None
    melee_weight: Optional[float] = None
    ranged_weight: Optional[float] = None
    speed_weight: Optional[float] = None
    status_effects_weight: Optional[float] = None
    status_effects: Optional[dict[str, float]] = None
    level_difference_threshold: Optional[float] = None
    level_difference_weight: Optional[float] = None


@dataclass
class AIOpponent:  # most of the time the player
    rules: dict[str, UserMonsterEntry]


@dataclass
class TechniqueCondition:
    turn: Optional[int] = None
    hp_below: Optional[float] = None
    hp_above: Optional[float] = None
    priority: Optional[int] = None
    always: Optional[bool] = False
    status_effects: Optional[list[str]] = None
    opponent_types: Optional[list[str]] = None
    opponent_slugs: Optional[list[str]] = None
    opponent_status: Optional[list[str]] = None
    hp_range: Optional[tuple[float, float]] = None


@dataclass
class MonsterTechnique:
    technique: str
    condition: Optional[TechniqueCondition]


@dataclass
class MonsterEntry:
    techniques: list[MonsterTechnique]


@dataclass
class AITrainers:
    trainers: dict[str, dict[str, MonsterEntry]]


@dataclass
class SingleTechnique:
    melee_bonus: Optional[float] = None
    touch_bonus: Optional[float] = None
    special_bonus: Optional[float] = None
    ranged_bonus: Optional[float] = None
    reach_bonus: Optional[float] = None
    reliable_bonus: Optional[float] = None
    power_weight: Optional[float] = None
    accuracy_weight: Optional[float] = None
    elemental_multiplier_weight: Optional[float] = None
    elemental_health_scaling: Optional[float] = None
    elemental_health_threshold: Optional[float] = None
    health_priority_threshold: Optional[float] = None
    healing_weight: Optional[float] = None
    healing_penalty_threshold: Optional[float] = None
    healing_penalty_weight: Optional[float] = None


@dataclass
class AITechniques:
    techniques: dict[str, SingleTechnique]


def load_yaml(filepath: Path) -> Any:
    try:
        with filepath.open() as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


class AIConfigLoader:
    _ai_techniques: Optional[AITechniques] = None
    _ai_items: Optional[AIItems] = None
    _ai_opponent: Optional[AIOpponent] = None
    _ai_character: Optional[AITrainers] = None

    @classmethod
    def get_ai_opponent(cls, filename: str) -> AIOpponent:
        yaml_path = paths.mods_folder / filename
        if cls._ai_opponent is None:
            raw_map = load_yaml(yaml_path)

            rules = {
                slug: UserMonsterEntry(**rules)
                for slug, rules in raw_map["rules"].items()
            }

            if "default" not in rules:
                raise ValueError(f"'default' is missing")

            cls._ai_opponent = AIOpponent(rules=rules)
        return cls._ai_opponent

    @classmethod
    def get_ai_items(cls, filename: str) -> AIItems:
        yaml_path = paths.mods_folder / filename
        if cls._ai_items is None:
            raw_map = load_yaml(yaml_path)
            cls._ai_items = AIItems(**raw_map)
        return cls._ai_items

    @classmethod
    def get_ai_character(cls, filename: str) -> AITrainers:
        yaml_path = paths.mods_folder / filename
        if cls._ai_character is None:
            raw_map = load_yaml(yaml_path)

            trainers = {
                character_slug: {
                    monster_slug: MonsterEntry(
                        techniques=[
                            MonsterTechnique(
                                technique=tech_data["technique"],
                                condition=(
                                    TechniqueCondition(
                                        **tech_data["condition"]
                                    )
                                    if "condition" in tech_data
                                    else None
                                ),
                            )
                            for tech_data in monster_data["techniques"]
                        ]
                    )
                    for monster_slug, monster_data in monsters.items()
                }
                for character_slug, monsters in raw_map["trainers"].items()
            }

            cls._ai_character = AITrainers(trainers=trainers)
        return cls._ai_character

    @classmethod
    def get_ai_techniques(cls, filename: str) -> AITechniques:
        yaml_path = paths.mods_folder / filename
        if cls._ai_techniques is None:
            raw_map = load_yaml(yaml_path)

            techniques = {
                key: SingleTechnique(**value)
                for key, value in raw_map["techniques"].items()
            }

            cls._ai_techniques = AITechniques(techniques=techniques)
        return cls._ai_techniques


class TechniqueTracker:
    def __init__(self, session: Session, moves: list[Technique]):
        self.session = session
        self.moves = moves

    def get_valid_moves(
        self, opponents: list[Monster]
    ) -> list[tuple[Technique, Monster]]:
        """Returns valid techniques and their corresponding opponents."""
        return [
            (mov, opponent)
            for mov in self.moves
            if not recharging(mov)
            for opponent in opponents
            if mov.validate_monster(self.session, opponent)
        ]

    def evaluate_technique(
        self,
        user: Monster,
        technique: Technique,
        opponent: Monster,
        config: SingleTechnique,
    ) -> float:
        """
        Evaluate the effectiveness of a technique against a specific opponent.
        """
        return technique_score(user, technique, opponent, config)


class OpponentEvaluator:
    def __init__(
        self, combat: CombatState, user: Monster, opponents: list[Monster]
    ):
        self.combat = combat
        self.user = user
        self.opponents = opponents
        self.ai_opponent = AIConfigLoader.get_ai_opponent("ai_opponent.yaml")

    def evaluate(self, opponent: Monster) -> float:
        """
        Scores opponents based on their current health, status effects, and power level.
        Higher scores indicate better targets.
        """
        if not self.combat.is_trainer_battle or not self.combat.is_double:
            return 1.0

        assert self.user.owner
        config = self.ai_opponent.rules.get(
            self.user.owner.slug, self.ai_opponent.rules.get("default")
        )

        if config is None:
            return 1.0

        return calculate_score(config, self.user, opponent)

    def get_best_target(self) -> Monster:
        """Returns the opponent with the highest evaluation score."""
        best_target = max(self.opponents, key=self.evaluate)
        logger.debug(f"Best target selected: {best_target.slug}")
        return best_target


class AIDecisionStrategy(ABC):
    def __init__(
        self, evaluator: OpponentEvaluator, tracker: TechniqueTracker
    ):
        self.evaluator = evaluator
        self.tracker = tracker
        self.ai_trainers = AIConfigLoader.get_ai_character("ai_trainers.yaml")
        self.ai_items = AIConfigLoader.get_ai_items("ai_items.yaml")
        self.ai_techs = AIConfigLoader.get_ai_techniques("ai_techniques.yaml")

    @abstractmethod
    def make_decision(self, ai: AI) -> None:
        pass

    @abstractmethod
    def select_move(
        self, ai: AI, target: Monster
    ) -> tuple[Technique, Monster]:
        pass

    def check_ai_techs(self, user: Monster) -> Optional[SingleTechnique]:
        _config = self.ai_techs
        if user.wild:
            config = _config.techniques.get(user.slug)
        else:
            assert user.owner
            config = _config.techniques.get(user.owner.slug)
        return config


class TrainerAIDecisionStrategy(AIDecisionStrategy):
    def make_decision(self, ai: AI) -> None:
        """Trainer battle decision-making"""
        character_slug = ai.character.slug
        config = self.ai_trainers.trainers.get(character_slug)

        if len(ai.character.items) > 0:
            for item in ai.character.items:
                if self.need_healing(ai, item):
                    ai.action_item(item)
                    return

        if config is None:
            self.default_decision(ai)
            return

        monster_config = config.get(ai.monster.slug)

        if monster_config is None:
            self.default_decision(ai)
            return

        if self.handle_monster_config(ai, monster_config):
            return

        valid_actions = self.tracker.get_valid_moves(ai.opponents)
        random_action = random.choice(valid_actions)
        ai.action_tech(random_action[0], random_action[1])

    def handle_monster_config(
        self, ai: AI, monster_config: MonsterEntry
    ) -> bool:
        """Handle decision-making logic for a specific monster configuration."""
        for technique_entry in monster_config.techniques:
            technique = technique_entry.technique
            condition = technique_entry.condition

            if condition is not None and not check_tech_conditions(
                condition, ai
            ):
                continue

            valid_actions = self.tracker.get_valid_moves(ai.opponents)
            for valid_technique, opponent in valid_actions:
                if valid_technique.slug == technique:
                    ai.action_tech(valid_technique, opponent)
                    return True

        return False

    def need_healing(self, ai: AI, item: Item) -> bool:
        """
        Determines if a healing item is needed based on the AI's monster's current state.
        """
        item_entry = self.ai_items.items.get(item.slug)
        if not item_entry:
            return False

        return check_item_conditions(item_entry, ai)

    def select_move(
        self, ai: AI, target: Monster
    ) -> tuple[Technique, Monster]:
        """Select the most effective move and target."""
        valid_actions = self.tracker.get_valid_moves(ai.opponents)

        if not valid_actions:
            skip = Technique.create("skip")
            return skip, target

        config = self.check_ai_techs(ai.monster)
        if config is None:
            return random.choice(valid_actions)

        best_action = None
        highest_score = 0.0

        for technique, opponent in valid_actions:
            score = self.tracker.evaluate_technique(
                ai.monster, technique, opponent, config
            )
            logger.debug(
                f"Score: {score}, Technique: {technique.slug}, Opponent: {opponent.slug}"
            )
            if score > highest_score:
                highest_score = score
                best_action = (technique, opponent)

        return best_action or random.choice(valid_actions)

    def default_decision(self, ai: AI) -> None:
        target = self.evaluator.get_best_target()
        technique, target = self.select_move(ai, target)
        ai.action_tech(technique, target)


class WildAIDecisionStrategy(AIDecisionStrategy):
    def make_decision(self, ai: AI) -> None:
        """Wild encounter decision-making: focus on moves."""
        target = self.evaluator.get_best_target()
        technique, target = self.select_move(ai, target)
        ai.action_tech(technique, target)

    def select_move(
        self, ai: AI, target: Monster
    ) -> tuple[Technique, Monster]:
        """Select the most effective move and target."""
        valid_actions = self.tracker.get_valid_moves(ai.opponents)

        if not valid_actions:
            skip = Technique.create("skip")
            return skip, target

        config = self.check_ai_techs(ai.monster)
        if config is None:
            return random.choice(valid_actions)

        best_action = None
        highest_score = 0.0

        for technique, opponent in valid_actions:
            score = self.tracker.evaluate_technique(
                ai.monster, technique, opponent, config
            )
            if score > highest_score:
                highest_score = score
                best_action = (technique, opponent)

        return best_action or random.choice(valid_actions)


class AI:
    def __init__(
        self,
        session: Session,
        combat: CombatState,
        monster: Monster,
        character: NPC,
    ) -> None:
        self.session = session
        self.combat = combat
        self.character = character
        self.monster = monster
        self.opponents: list[Monster] = (
            combat.monsters_in_play[combat.players[1]]
            if character == combat.players[0]
            else combat.monsters_in_play[combat.players[0]]
        )

        self.evaluator = OpponentEvaluator(
            self.combat, self.monster, self.opponents
        )
        self.tracker = TechniqueTracker(self.session, self.monster.moves)

        self.decision_strategy = (
            TrainerAIDecisionStrategy(self.evaluator, self.tracker)
            if self.combat.is_trainer_battle
            else WildAIDecisionStrategy(self.evaluator, self.tracker)
        )

        self.decision_strategy.make_decision(self)

    def get_available_moves(self) -> list[tuple[Technique, Monster]]:
        """
        Use TechniqueTracker to get valid moves.
        """
        return self.tracker.get_valid_moves(self.opponents)

    def evaluate_best_opponent(self) -> Monster:
        """
        Use OpponentEvaluator to find the best target opponent.
        """
        return self.evaluator.get_best_target()

    def action_tech(self, technique: Technique, target: Monster) -> None:
        """
        Send action tech.
        """
        self.character.game_variables["action_tech"] = technique.slug
        technique = pre_checking(
            self.session, self.monster, technique, target, self.combat
        )
        self.combat.enqueue_action(self.monster, technique, target)

    def action_item(self, item: Item) -> None:
        """
        Send action item.
        """
        self.combat.enqueue_action(self.character, item, self.monster)


def check_item_conditions(item_entry: ItemEntry, ai: AI) -> bool:
    """
    Check if all conditions for a technique are met.
    """
    hp_ratio = ai.monster.hp_ratio

    if item_entry.hp_below and hp_ratio >= item_entry.hp_below:
        return False

    if item_entry.hp_above and hp_ratio <= item_entry.hp_above:
        return False

    if item_entry.hp_range and not (
        item_entry.hp_range[0] <= hp_ratio < item_entry.hp_range[1]
    ):
        return False

    if item_entry.status_effects and not any(
        has_status(ai.monster, status) for status in item_entry.status_effects
    ):
        return False

    if (
        item_entry.monster_slugs
        and ai.monster.slug not in item_entry.monster_slugs
    ):
        return False

    return True


def check_tech_conditions(condition: TechniqueCondition, ai: AI) -> bool:
    """
    Check if all conditions for a technique are met.
    """
    current_turn = ai.combat._turn
    monster_health = ai.monster.hp_ratio

    if condition.always:
        return True

    if condition.turn is not None and current_turn != condition.turn:
        return False

    if condition.hp_below is not None and monster_health >= condition.hp_below:
        return False

    if condition.hp_above is not None and monster_health <= condition.hp_above:
        return False

    if condition.hp_range and not (
        condition.hp_range[0] <= monster_health <= condition.hp_range[1]
    ):
        return False

    if condition.status_effects:
        return any(
            has_status(ai.monster, status)
            for status in condition.status_effects
        )

    if condition.opponent_status:
        if not ai.combat.is_double:
            return any(
                has_status(ai.opponents[0], opponent_status)
                for opponent_status in condition.opponent_status
            )

    if condition.opponent_types:
        if not ai.combat.is_double:
            return any(
                ai.opponents[0].has_type(opponent_type)
                for opponent_type in condition.opponent_types
            )

    if condition.opponent_slugs:
        if not ai.combat.is_double:
            return ai.opponents[0].slug in condition.opponent_slugs

    return True


def calculate_score(
    config: UserMonsterEntry, user: Monster, opponent: Monster
) -> float:
    """Calculate score."""
    health_score = 0.0
    armour_score = 0.0
    dodge_score = 0.0
    melee_score = 0.0
    ranged_score = 0.0
    speed_score = 0.0
    status_effect_score = 0.0
    level_difference_score = 0.0

    monster_health = opponent.hp_ratio

    if config.health_weight:
        health_score = monster_health * config.health_weight
    if config.armour_weight:
        armour_score = opponent.armour * config.armour_weight
    if config.dodge_weight:
        dodge_score = opponent.dodge * config.dodge_weight
    if config.melee_weight:
        melee_score = opponent.melee * config.melee_weight
    if config.ranged_weight:
        ranged_score = opponent.ranged * config.ranged_weight
    if config.speed_weight:
        speed_score = opponent.speed * config.speed_weight

    if config.status_effects and config.status_effects_weight:
        for status in opponent.status:
            if status.slug in config.status_effects:
                status_effect_score += (
                    config.status_effects.get(status.slug, 1.0)
                    * config.status_effects_weight
                )

    if config.level_difference_threshold and config.level_difference_weight:
        level_difference = opponent.level - user.level
        if abs(level_difference) >= config.level_difference_threshold:
            level_difference_score = (
                level_difference * config.level_difference_weight
            )

    total_score = (
        health_score
        + armour_score
        + dodge_score
        + melee_score
        + ranged_score
        + speed_score
        + status_effect_score
        + level_difference_score
    )
    logger.debug(f"Health score: {health_score}")
    logger.debug(f"Armour score: {armour_score}")
    logger.debug(f"Dodge score: {dodge_score}")
    logger.debug(f"Melee score: {melee_score}")
    logger.debug(f"Ranged score: {ranged_score}")
    logger.debug(f"Speed score: {speed_score}")
    logger.debug(f"Status effect score: {status_effect_score}")
    logger.debug(f"Level difference score: {level_difference_score}")
    logger.debug(f"Final total score: {total_score}")
    return total_score


def technique_score(
    user: Monster,
    technique: Technique,
    opponent: Monster,
    config: SingleTechnique,
) -> float:
    """Technique score."""
    effectiveness_score = 0.0
    type_bonus = 0.0
    power_score = 0.0
    accuracy_score = 0.0
    healing_score = 0.0

    if config.elemental_multiplier_weight:
        effectiveness_score = (
            simple_damage_multiplier(technique.types, opponent.types)
            * config.elemental_multiplier_weight
        )

    elemental_health = config.elemental_health_threshold
    elemental_scaling = config.elemental_health_scaling
    if elemental_health and elemental_scaling:
        if opponent.current_hp > opponent.hp * elemental_health:
            effectiveness_score *= elemental_scaling

    type_bonus += getattr(config, f"{technique.range}_bonus", 0.0)

    if config.power_weight:
        normalized_power = technique.power / prepare.POWER_RANGE[1]
        power_score = normalized_power * config.power_weight

    if config.accuracy_weight:
        accuracy_score = technique.accuracy * config.accuracy_weight

    health_priority = config.health_priority_threshold
    healing_penalty = config.healing_penalty_threshold
    healing_weight = config.healing_weight
    healing_penalty_weight = config.healing_penalty_weight
    if health_priority:
        if technique.healing_power > 0.0 or technique.power == 0.0:
            if user.hp_ratio < health_priority and healing_weight:
                # Reward healing when health is below the priority threshold
                healing_score = technique.healing_power * healing_weight

    if healing_penalty:
        if technique.healing_power > 0.0 or technique.power == 0.0:
            if user.hp_ratio > healing_penalty and healing_penalty_weight:
                # Penalize healing when health is above the penalty threshold
                healing_score = (
                    -technique.healing_power * healing_penalty_weight
                )

    total_score = (
        effectiveness_score
        + type_bonus
        + power_score
        + accuracy_score
        + healing_score
    )
    logger.debug(f"Elemental effectiveness score: {effectiveness_score}")
    logger.debug(f"Type bonus for range '{technique.range}': {type_bonus}")
    logger.debug(f"Power score (normalized): {power_score}")
    logger.debug(f"Accuracy score: {accuracy_score}")
    logger.debug(f"Healing score: {healing_score}")
    logger.debug(f"Final technique score: {total_score}")

    return total_score
