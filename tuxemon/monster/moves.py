# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tuxemon.db import (
    LearningMethod,
    MonsterMovesetItemModel,
)
from tuxemon.technique.technique import Technique, decode_moves, encode_moves

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


class MonsterMovesHandler:
    def __init__(
        self,
        moves: list[Technique] | None = None,
        moveset: Sequence[MonsterMovesetItemModel] | None = None,
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

    def apply_item_techniques(self, monster: Monster, item: Item) -> None:
        for tech_slug in item.granted_techniques:
            if not self.has_move(tech_slug):
                monster.max_moves += 1
                self.add_move(Technique.create(tech_slug))

    def remove_item_techniques(self, monster: Monster, item: Item) -> None:
        granted = set(item.granted_techniques)
        removed = sum(1 for m in self.moves if m.slug in granted)
        self.moves = [m for m in self.moves if m.slug not in granted]

        monster.max_moves -= removed
        if monster.max_moves < 0:
            monster.max_moves = 0

    def learn(
        self,
        monster: Monster,
        technique: Technique,
        max_moves: int | None = None,
        method: LearningMethod | None = None,
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
        if max_moves is None:
            max_moves = monster.max_moves

        if not ignore_eligibility and not self.can_learn(
            monster, technique, max_moves, method
        ):
            return False

        if len(self.moves) >= max_moves:
            # The moveset is full. The existing code handles this by appending
            # the move anyway, but we are going to implement pending moves here.
            # self.pending_moves.setdefault(monster.iid, []).append(technique.slug)
            self.moves.append(technique)
        else:
            self.moves.append(technique)
        return True

    def can_learn(
        self,
        monster: Monster,
        technique: Technique,
        max_moves: int | None = None,
        method: LearningMethod | None = None,
    ) -> bool:
        if max_moves is None:
            max_moves = monster.max_moves
        if not self.is_technique_eligible(monster, technique, method):
            return False
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
        method: LearningMethod | None = None,
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
        method: LearningMethod | None = None,
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
        max_moves: int | None = None,
        method: LearningMethod | None = None,
    ) -> None:
        """
        Set monster moves according to its current level and evolution stage.

        Parameters:
            monster: The monster instance.
            max_moves: The maximum number of moves the monster can have at once.
            method: The method by which the monster learns moves.
        """
        if max_moves is None:
            max_moves = monster.max_moves

        if method is None:
            method = LearningMethod.LEVEL_UP

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

    def techniques_learned_between(
        self, start_level: int, end_level: int
    ) -> list[str]:
        return [
            move.technique
            for move in self.moveset
            if start_level < move.level_learned <= end_level
        ]

    def preview_moves_learned(
        self,
        monster: Monster,
        levels_earned: int,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> list[str]:
        start_level = monster.level - levels_earned
        techniques = self.techniques_learned_between(
            start_level, monster.level
        )

        learnable = []
        for tech in techniques:
            technique = Technique.create(tech)

            if self.can_learn(monster, technique, method=method):
                learnable.append(tech)

        return learnable

    def update_moves(
        self,
        monster: Monster,
        levels_earned: int,
        method: LearningMethod = LearningMethod.LEVEL_UP,
    ) -> list[Technique]:
        start_level = monster.level - levels_earned
        techniques = self.techniques_learned_between(
            start_level, monster.level
        )

        newly_learned = []
        for tech in techniques:
            technique = Technique.create(tech)
            if self.learn(monster, technique, method=method):
                newly_learned.append(technique)

        return newly_learned

    def learn_by_method(
        self,
        monster: Monster,
        technique_slug: str,
        methods: LearningMethod | set[LearningMethod],
    ) -> Technique | None:
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

    def reset_current_stats(self) -> None:
        for move in self.moves:
            move.reset_current_stats()

    def find_tech_by_id(self, instance_id: UUID) -> Technique | None:
        """Finds a technique among the monster's moves which has the given id."""
        return next(
            (m for m in self.moves if m.instance_id == instance_id), None
        )

    def _get_moveset_entry(
        self, technique: Technique
    ) -> MonsterMovesetItemModel | None:
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

    def get_usable_moves(
        self, session: Session, opponents: Sequence[Monster]
    ) -> list[Technique]:
        usable = []
        for tech in self.moves:
            if any(tech.can_use(session, target) for target in opponents):
                usable.append(tech)
        return usable

    def get_pending_moves(self, monster_iid: UUID) -> list[str]:
        return self.pending_moves.get(monster_iid, [])

    def get_fallback_moves(self) -> list[Technique]:
        return [
            Technique.create(m.technique)
            for m in self.moveset
            if m.learning_method == LearningMethod.FALLBACK
        ]

    def clear_pending_moves(self, monster_iid: UUID) -> None:
        self.pending_moves.pop(monster_iid, None)

    def encode_moves(self) -> Sequence[Mapping[str, Any]]:
        return encode_moves(self.moves)

    def decode_moves(self, json_data: Mapping[str, Any] | None) -> None:
        if json_data is None or "moves" not in json_data:
            return
        self.moves = [mov for mov in decode_moves(json_data["moves"])]
