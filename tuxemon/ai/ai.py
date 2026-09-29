# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.ai.decision_strategy import (
    TrainerAIDecisionStrategy,
    WildAIDecisionStrategy,
)
from tuxemon.ai.opponent_evaluator import OpponentEvaluator
from tuxemon.ai.technique_tracker import TechniqueTracker
from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class ItemEntry:
    hp_below: float | None = None
    hp_above: float | None = None
    hp_range: tuple[float, float] | None = None
    status_effects: list[str] | None = None
    monster_slugs: list[str] | None = None


@dataclass
class AIItems:
    items: dict[str, ItemEntry]


@dataclass
class UserMonsterEntry:
    health_weight: float | None = None
    armour_weight: float | None = None
    dodge_weight: float | None = None
    melee_weight: float | None = None
    ranged_weight: float | None = None
    speed_weight: float | None = None
    status_effects_weight: float | None = None
    status_effects: dict[str, float] | None = None
    level_difference_threshold: float | None = None
    level_difference_weight: float | None = None


@dataclass
class AIOpponent:  # most of the time the player
    rules: dict[str, UserMonsterEntry]


@dataclass
class TechniqueCondition:
    turn: int | None = None
    hp_below: float | None = None
    hp_above: float | None = None
    priority: int | None = None
    always: bool | None = False
    status_effects: list[str] | None = None
    opponent_types: list[str] | None = None
    opponent_slugs: list[str] | None = None
    opponent_status: list[str] | None = None
    hp_range: tuple[float, float] | None = None


@dataclass
class MonsterTechnique:
    technique: str
    condition: TechniqueCondition | None


@dataclass
class MonsterEntry:
    techniques: list[MonsterTechnique]


@dataclass
class AITrainers:
    trainers: dict[str, dict[str, MonsterEntry]]


@dataclass
class SingleTechnique:
    melee_bonus: float | None = None
    touch_bonus: float | None = None
    special_bonus: float | None = None
    ranged_bonus: float | None = None
    reach_bonus: float | None = None
    reliable_bonus: float | None = None
    power_weight: float | None = None
    accuracy_weight: float | None = None
    elemental_multiplier_weight: float | None = None
    elemental_health_scaling: float | None = None
    elemental_health_threshold: float | None = None
    health_priority_threshold: float | None = None
    healing_weight: float | None = None
    healing_penalty_threshold: float | None = None
    healing_penalty_weight: float | None = None


@dataclass
class AITechniques:
    techniques: dict[str, SingleTechnique]


class AIConfigLoader:
    _ai_techniques: AITechniques | None = None
    _ai_items: AIItems | None = None
    _ai_opponent: AIOpponent | None = None
    _ai_character: AITrainers | None = None

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
                raise ValueError("'default' is missing")

            cls._ai_opponent = AIOpponent(rules=rules)
        return cls._ai_opponent

    @classmethod
    def get_ai_items(cls, filename: str) -> AIItems:
        yaml_path = paths.mods_folder / filename
        if cls._ai_items is None:
            raw_map = load_yaml(yaml_path)

            items = {
                slug: ItemEntry(**entry)
                for slug, entry in raw_map["items"].items()
            }

            cls._ai_items = AIItems(items=items)

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


class AI:
    def __init__(
        self,
        session: Session,
        monster: Monster,
        character: NPC,
    ) -> None:
        self.session = session
        self.combat_session = session.client.combat_session
        self.character = character
        self.monster = monster
        self.opponents: list[Monster] = (
            self.combat_session.field_monsters.get_monsters(
                self.combat_session.right_player
            )
            if character == self.combat_session.left_player
            else self.combat_session.field_monsters.get_monsters(
                self.combat_session.left_player
            )
        )

        self.ai_opponent = AIConfigLoader.get_ai_opponent("ai_opponent.yaml")
        self.evaluator = OpponentEvaluator(
            self.session, self.monster, self.opponents, self.ai_opponent
        )
        self.tracker = TechniqueTracker(
            self.session, self.monster.moves.get_moves()
        )

        self.ai_trainers = AIConfigLoader.get_ai_character("ai_trainers.yaml")
        self.ai_items = AIConfigLoader.get_ai_items("ai_items.yaml")
        self.ai_techs = AIConfigLoader.get_ai_techniques("ai_techniques.yaml")

        self.decision_strategy = (
            TrainerAIDecisionStrategy(
                self.evaluator,
                self.tracker,
                self.ai_trainers,
                self.ai_items,
                self.ai_techs,
            )
            if self.combat_session.is_trainer_battle
            else WildAIDecisionStrategy(
                self.evaluator,
                self.tracker,
                self.ai_trainers,
                self.ai_items,
                self.ai_techs,
            )
        )

    def take_turn(self) -> None:
        """
        Causes this AI monster to make and execute its decision for the current turn.
        """
        self.decision_strategy.make_decision(self)

    def get_available_moves(self) -> list[tuple[Technique, Monster]]:
        """Use TechniqueTracker to get valid moves."""
        return self.tracker.get_valid_moves(self.opponents)

    def evaluate_best_opponent(self) -> Monster:
        """Use OpponentEvaluator to find the best target opponent."""
        return self.evaluator.get_best_target()

    def action_tech(self, technique: Technique, target: Monster) -> None:
        """
        Send action tech.
        """
        self.combat_session.set_variable("action_tech", technique.slug)
        technique = self.combat_session.pre_checking(
            self.session, self.monster, technique, target
        )
        self.combat_session.enqueue_action(self.monster, technique, target)

    def action_item(self, item: Item) -> None:
        """
        Send action item.
        """
        self.combat_session.enqueue_action(self.character, item, self.monster)
