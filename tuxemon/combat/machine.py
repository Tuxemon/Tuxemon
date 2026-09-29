# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.combat.session import CombatSession


logger = logging.getLogger()


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


class CombatMachine:
    def __init__(self, session: CombatSession):
        self.session = session

    def determine_next_phase(
        self, current_phase: CombatPhase | None
    ) -> CombatPhase | None:
        logger.debug(f"Evaluating next phase from: {current_phase}")

        if current_phase is None or current_phase == CombatPhase.BEGIN:
            logger.debug("Phase is None or BEGIN — no transition.")
            return None

        elif current_phase == CombatPhase.READY:
            logger.debug("Transitioning to HOUSEKEEPING.")
            return CombatPhase.HOUSEKEEPING

        elif current_phase == CombatPhase.HOUSEKEEPING:
            for player in self.session.active_players:
                positions_available = self.session.get_available_positions(
                    player
                )
                if positions_available:
                    logger.debug(
                        f"Player {player} has available positions — waiting."
                    )
                    return None
            logger.debug("All positions filled — transitioning to DECISION.")
            return CombatPhase.DECISION

        elif current_phase == CombatPhase.DECISION:
            if len(self.session.remaining_players) == 1:
                logger.debug(
                    "Only one player remaining — transitioning to RAN_AWAY."
                )
                return CombatPhase.RAN_AWAY
            # A monster may have zero, one or more than one action. Charging,
            # locked and disappeared monsters skip the decision phase because
            # the effect that put them in that state already scheduled their
            # action on the pending queue, so they count as decided without
            # appearing in the queue. Pending actions are deliberately not
            # counted on their own: a monster that used foresight in an
            # earlier round still picks a new action even though it has
            # another one coming, and must not be treated as decided.
            queue = self.session.action_queue.queue
            active = set(self.session.active_monsters)
            committed = {m for m in active if self.session.skips_decision(m)}
            committed |= active & {action.user for action in queue}
            # An action whose user is the trainer rather than a monster
            # (e.g. throwing a tuxeball or using another item) consumes one
            # of that trainer's monsters' turns, even though no monster
            # appears as the action's user. Count each such action as
            # covering one of the trainer's undecided monsters.
            for player in self.session.active_players:
                npc_actions = sum(1 for a in queue if a.user == player)
                if npc_actions:
                    monsters = self.session.field_monsters.get_monsters(player)
                    uncovered = [m for m in monsters if m not in committed]
                    committed.update(uncovered[:npc_actions])
            if active and active <= committed:
                logger.debug(
                    "All monsters have actions — transitioning to PRE_ACTION."
                )
                return CombatPhase.PRE_ACTION
            logger.debug("Waiting for decisions.")
            return None

        elif current_phase == CombatPhase.PRE_ACTION:
            logger.debug("Transitioning to ACTION.")
            return CombatPhase.ACTION

        elif current_phase == CombatPhase.ACTION:
            if self.session.action_queue.is_empty():
                logger.debug(
                    "Action queue empty — transitioning to POST_ACTION."
                )
                return CombatPhase.POST_ACTION
            logger.debug("Processing actions.")
            return None

        elif current_phase == CombatPhase.POST_ACTION:
            if self.session.action_queue.is_empty():
                logger.debug(
                    "Post-action queue empty — transitioning to RESOLVE_MATCH."
                )
                return CombatPhase.RESOLVE_MATCH
            logger.debug("Processing post-actions.")
            return None

        elif current_phase == CombatPhase.RESOLVE_MATCH:
            remaining = len(self.session.remaining_players)
            logger.debug(f"Resolving match — {remaining} players remaining.")
            if remaining == 0:
                logger.debug(
                    "No players remaining — transitioning to DRAW_MATCH."
                )
                return CombatPhase.DRAW_MATCH
            elif remaining == 1:
                run = self.session.get_variable("run")
                if run:
                    logger.debug("Player ran — transitioning to RAN_AWAY.")
                    return CombatPhase.RAN_AWAY
                else:
                    logger.debug(
                        "One player left — transitioning to HAS_WINNER."
                    )
                    return CombatPhase.HAS_WINNER
            else:
                logger.debug(
                    "Multiple players remain — transitioning to HOUSEKEEPING."
                )
                return CombatPhase.HOUSEKEEPING

        elif current_phase in {
            CombatPhase.RAN_AWAY,
            CombatPhase.DRAW_MATCH,
            CombatPhase.HAS_WINNER,
            CombatPhase.END_COMBAT,
        }:
            logger.debug(
                f"Phase {current_phase} reached — transitioning to END_COMBAT."
            )
            return CombatPhase.END_COMBAT

        else:
            raise ValueError(f"Unexpected phase: {current_phase}")
