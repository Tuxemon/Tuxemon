# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from tuxemon import prepare
from tuxemon.db import (
    EvolutionStage,
    LearningMethod,
    MonsterMovesetItemModel,
)
from tuxemon.technique.technique import Technique, decode_moves, encode_moves

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


class MonsterMovesHandler:
    def __init__(
        self,
        moves: Optional[list[Technique]] = None,
        moveset: Optional[Sequence[MonsterMovesetItemModel]] = None,
    ):
        self.moves = moves if moves is not None else []
        self.moveset = list(moveset) if moveset is not None else []

    @property
    def current_moves(self) -> list[Technique]:
        return self.moves

    def set_moveset(self, moveset: Sequence[MonsterMovesetItemModel]) -> None:
        """Sets the raw moveset data from the database."""
        self.moveset = list(moveset)

    def learn(self, technique: Technique) -> None:
        """
        Adds a technique to this tuxemon's moveset.

        Parameters:
            technique: The technique for the monster to learn.
        """

        self.moves.append(technique)

    def forget(self, technique: Technique) -> bool:
        """
        Removes a technique from the monster's moveset.

        Parameters:
            technique: The technique to forget.
        """
        moveset_entry = next(
            (m for m in self.moveset if m.technique == technique.slug), None
        )
        if moveset_entry and not moveset_entry.can_be_forgotten:
            return False
        if technique in self.moves:
            self.moves.remove(technique)
            return True
        return False

    def is_move_eligible(
        self,
        move: MonsterMovesetItemModel,
        level: int,
        evolution_stage: Optional[EvolutionStage] = None,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> bool:
        if move.learning_method != method:
            return False
        return move.level_learned <= level and (
            move.evolution_stage_learned is None
            or (
                evolution_stage is not None
                and move.evolution_stage_learned == evolution_stage
            )
        )

    def can_forget(self, technique: Technique) -> bool:
        entry = next(
            (m for m in self.moveset if m.technique == technique.slug), None
        )
        return entry is not None and entry.can_be_forgotten

    def remove_forced(self, technique: Technique) -> bool:
        if technique in self.moves:
            self.moves.remove(technique)
            return True
        return False

    def replace_move(self, index: int, new_move: Technique) -> None:
        """
        Replaces a move at a given index with a new technique.

        Parameters:
            index: The position of the move to replace.
            new_move: The new technique to insert.
        """
        if 0 <= index < len(self.moves):
            self.moves[index] = new_move

    def set_moves(
        self,
        level: int,
        evolution_stage: Optional[EvolutionStage] = None,
        max_moves: int = prepare.MAX_MOVES,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> None:
        """
        Set monster moves according to the level.

        Parameters:
            level: The current level of the monster.
            evolution_stage: The monster's current evolution stage,
                if applicable.
            max_moves: The maximum number of moves the monster can have
                at once.
            method: The method by which the monster learns moves
                (e.g., LEVEL_UP, EVOLUTION).
        """
        eligible_moves = [
            move.technique
            for move in self.moveset
            if self.is_move_eligible(
                move=move,
                level=level,
                method=method,
                evolution_stage=evolution_stage,
            )
        ]

        moves_to_learn = eligible_moves[-max_moves:]
        for move_name in moves_to_learn:
            technique = Technique.create(move_name)
            self.learn(technique)
            logger.debug(
                f"Monster learned technique: {technique.slug} at level {level} and stage {evolution_stage}"
            )

    def update_moves(
        self,
        monster_level: int,
        levels_earned: int,
        evolution_stage: Optional[EvolutionStage] = None,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> list[Technique]:
        start_level = monster_level - levels_earned
        new_techniques = []

        for move in self.moveset:
            if (
                start_level < move.level_learned <= monster_level
                and self.is_move_eligible(
                    move=move,
                    level=monster_level,
                    evolution_stage=evolution_stage,
                    method=method,
                )
                and move.technique not in (m.slug for m in self.moves)
            ):
                technique = Technique.create(move.technique)
                self.moves.append(technique)
                new_techniques.append(technique)
                logger.debug(
                    f"Monster learned new technique: {technique.slug} between levels {start_level}-{monster_level} and stage {evolution_stage} via {method.name}"
                )

        return new_techniques

    def learn_by_method(
        self,
        technique_slug: str,
        methods: Union[LearningMethod, set[LearningMethod]],
    ) -> Optional[Technique]:
        if isinstance(methods, LearningMethod):
            methods = {methods}

        move_data = next(
            (m for m in self.moveset if m.technique == technique_slug), None
        )

        if not move_data or move_data.learning_method not in methods:
            return None

        technique = Technique.create(technique_slug)
        self.learn(technique)
        logger.debug(
            f"Monster learned technique via {move_data.learning_method.value.upper()}: {technique_slug}"
        )
        return technique

    def recharge_moves(self) -> None:
        for move in self.moves:
            move.recharge()

    def full_recharge_moves(self) -> None:
        for move in self.moves:
            move.full_recharge()

    def set_stats(self) -> None:
        for move in self.moves:
            move.set_stats()

    def find_tech_by_id(self, instance_id: UUID) -> Optional[Technique]:
        """Finds a technique among the monster's moves which has the given id."""
        return next(
            (m for m in self.moves if m.instance_id == instance_id), None
        )

    def has_moves(self) -> bool:
        return bool(self.moves)

    def has_move(self, move_slug: str) -> bool:
        return any(move.slug == move_slug for move in self.get_moves())

    def get_moves(self) -> list[Technique]:
        return self.moves

    def encode_moves(self) -> Sequence[Mapping[str, Any]]:
        return encode_moves(self.moves)

    def decode_moves(self, json_data: Optional[Mapping[str, Any]]) -> None:
        if json_data and "moves" in json_data:
            self.moves = [mov for mov in decode_moves(json_data["moves"])]
