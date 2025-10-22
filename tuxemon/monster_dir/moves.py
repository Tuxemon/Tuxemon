# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from tuxemon import prepare
from tuxemon.db import (
    LearningMethod,
    MonsterMovesetItemModel,
)
from tuxemon.technique.technique import Technique, decode_moves, encode_moves

if TYPE_CHECKING:
    from tuxemon.monster import Monster


logger = logging.getLogger(__name__)


class MonsterMovesHandler:
    def __init__(
        self,
        moves: Optional[list[Technique]] = None,
        moveset: Optional[Sequence[MonsterMovesetItemModel]] = None,
    ):
        self.moves = moves if moves is not None else []
        self.moveset = list(moveset) if moveset is not None else []
        self.pending_moves: dict[UUID, list[str]] = {}

    @property
    def current_moves(self) -> list[Technique]:
        return self.moves

    def set_moveset(self, moveset: Sequence[MonsterMovesetItemModel]) -> None:
        """Sets the raw moveset data from the database."""
        self.moveset = list(moveset)

    def add_move(self, technique: Technique) -> None:
        """
        Adds a technique to this tuxemon's moveset.
        """
        self.moves.append(technique)

    def learn(
        self,
        monster: Monster,
        technique: Technique,
        max_moves: int = prepare.MAX_MOVES,
        method: Optional[LearningMethod] = None,
        ignore_eligibility: bool = False,
    ) -> bool:
        """
        Adds a technique to this tuxemon's moveset, after checking for eligibility.

        Parameters:
            monster: The monster instance.
            technique: The technique to learn.
            max_moves: The maximum number of moves the monster can have.
            method: The method by which the monster learns the move.
            ignore_eligibility: If True, skips the eligibility check.

        Returns:
            True if the technique was learned, False otherwise.
        """
        if not ignore_eligibility and not self.is_technique_eligible(
            monster, technique, method
        ):
            return False

        if len(self.moves) >= max_moves:
            # The moveset is full. The existing code handles this by appending
            # the move anyway, but we are going to implement pending moves here.
            # self.pending_moves.setdefault(monster.iid, []).append(technique.slug)
            self.moves.append(technique)
        else:
            self.moves.append(technique)

        logger.debug(f"Monster learned technique: {technique.slug}")
        return True

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

    def is_eligible(
        self,
        monster: Monster,
        technique_slug: str,
        method: Optional[LearningMethod] = None,
    ) -> bool:
        move_data = next(
            (m for m in self.moveset if m.technique == technique_slug), None
        )

        if move_data is None:
            logger.debug(
                f"Move '{technique_slug}' not eligible: Not found in moveset."
            )
            return False

        if method is not None and move_data.learning_method != method:
            logger.debug(
                f"Move '{technique_slug}' not eligible: Wrong method. Expected '{method.name}', got '{move_data.learning_method.name}'."
            )
            return False

        if (
            move_data.evolution_stage_learned is not None
            and move_data.evolution_stage_learned != monster.stage
        ):
            logger.debug(
                f"Move '{technique_slug}' not eligible: Wrong evolution stage."
            )
            return False

        if move_data.level_learned > monster.level:
            logger.debug(
                f"Move '{technique_slug}' not eligible: Monster level is too low."
            )
            return False

        return True

    def is_technique_eligible(
        self,
        monster: Monster,
        technique: Technique,
        method: Optional[LearningMethod] = None,
    ) -> bool:
        """
        Checks if a Technique object is eligible for a monster to learn.

        Parameters:
            monster: The monster instance.
            technique: The Technique object to check.
            method: The expected learning method (e.g., LEVEL_UP, EVOLUTION).

        Returns:
            True if the technique is eligible, False otherwise.
        """
        return self.is_eligible(monster, technique.slug, method)

    def can_forget(self, technique: Technique) -> bool:
        entry = self._get_moveset_entry(technique)

        if entry is None:
            logger.debug(
                f"Technique '{technique.slug}' not found in moveset — assuming it can be forgotten."
            )
            return True

        if not entry.can_be_forgotten:
            logger.debug(
                f"Technique '{technique.slug}' is marked as non-forgettable."
            )
            return False

        logger.debug(f"Technique '{technique.slug}' can be forgotten.")
        return True

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
        monster: Monster,
        max_moves: int = prepare.MAX_MOVES,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> None:
        """
        Set monster moves according to its current level and evolution stage.

        Parameters:
            monster: The monster instance.
            max_moves: The maximum number of moves the monster can have at once.
            method: The method by which the monster learns moves.
        """
        eligible_moves = [
            move.technique
            for move in self.moveset
            if self.is_eligible(monster, move.technique, method)
        ]

        moves_to_learn = eligible_moves[-max_moves:]
        for move_name in moves_to_learn:
            technique = Technique.create(move_name)
            if self.learn(
                monster, technique, max_moves=max_moves, method=method
            ):
                logger.debug(
                    f"Monster '{monster.slug}' learned technique: {technique.slug} at level {monster.level} and stage {monster.stage}"
                )

    def update_moves(
        self,
        monster: Monster,
        levels_earned: int,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> list[Technique]:
        start_level = monster.level - levels_earned
        newly_learned_techniques = []

        for move in self.moveset:
            if start_level < move.level_learned <= monster.level:
                technique = Technique.create(move.technique)

                if self.learn(monster, technique, method=method):
                    newly_learned_techniques.append(technique)

        return newly_learned_techniques

    def learn_by_method(
        self,
        monster: Monster,
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

        if self.learn(monster, technique, method=move_data.learning_method):
            logger.debug(
                f"Monster learned technique via {move_data.learning_method.value.upper()}: {technique_slug}"
            )
            return technique

        return None

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

    def _get_moveset_entry(
        self, technique: Technique
    ) -> Optional[MonsterMovesetItemModel]:
        """Finds the moveset entry for a given technique."""
        return next(
            (m for m in self.moveset if m.technique == technique.slug), None
        )

    def replace_all_moves(self, new_moves: list[Technique]) -> None:
        """
        Replaces the monster's current moveset with a new list of techniques.
        """
        self.moves = new_moves
        logger.info("Monster's moveset has been completely replaced.")

    def has_moves(self) -> bool:
        return bool(self.moves)

    def has_move(self, move_slug: str) -> bool:
        return any(move.slug == move_slug for move in self.get_moves())

    def get_moves(self) -> list[Technique]:
        return self.moves

    def get_pending_moves(self, monster_iid: UUID) -> list[str]:
        return self.pending_moves.get(monster_iid, [])

    def clear_pending_moves(self, monster_iid: UUID) -> None:
        self.pending_moves.pop(monster_iid, None)

    def encode_moves(self) -> Sequence[Mapping[str, Any]]:
        return encode_moves(self.moves)

    def decode_moves(self, json_data: Optional[Mapping[str, Any]]) -> None:
        if json_data and "moves" in json_data:
            self.moves = [mov for mov in decode_moves(json_data["moves"])]
