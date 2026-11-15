# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)

# Game variable holding the money method of the campaign in play. A campaign
# that wants a formula other than the default sets it in its own event
# script, and the choice is saved with the game.
MONEY_METHOD_VARIABLE = "method_money"


class MoneyMethod(Enum):
    """Formula used to calculate the prize money for a defeated monster."""

    PARTICIPANT_SCALED = "participant_scaled"
    CONSERVED = "conserved"


DEFAULT_MONEY_METHOD = MoneyMethod.PARTICIPANT_SCALED


def calculate_money_base(level: int, money_modifier: float) -> int:
    """Base bounty formula used by all strategies."""
    return int(level * money_modifier)


class MoneyStrategy(ABC):
    name: ClassVar[MoneyMethod]

    @abstractmethod
    def calculate(
        self, loser: Monster, participants: Iterable[Monster]
    ) -> int:
        """Return the prize paid out for defeating the loser."""


class ParticipantScaledMoneyStrategy(MoneyStrategy):
    """
    The bounty is paid once per monster that took part in the defeat.

    Prize: base_money * winner_multiplier * loser_multiplier, summed over
        every participant.
    Notes: the more monsters join a fight, the more money it pays. Fainted
        participants are skipped, so surviving the fight is what earns a
        share. This is the historical Tuxemon formula.
    """

    name: ClassVar[MoneyMethod] = MoneyMethod.PARTICIPANT_SCALED

    def calculate(
        self, loser: Monster, participants: Iterable[Monster]
    ) -> int:
        return sum(
            self._share(loser, participant)
            for participant in participants
            if participant.owner
            and participant.owner.is_player
            and not participant.is_fainted
        )

    def _share(self, loser: Monster, winner: Monster) -> int:
        base_money = calculate_money_base(loser.level, loser.money_modifier)

        winner_multiplier = 1.0
        loser_multiplier = 1.0

        if winner.held_item and winner.held_item.money_multiplier:
            winner_multiplier = winner.held_item.money_multiplier

        if loser.held_item and loser.held_item.money_multiplier:
            loser_multiplier = loser.held_item.money_multiplier

        return int(base_money * winner_multiplier * loser_multiplier)


class ConservedMoneyStrategy(MoneyStrategy):
    """
    The bounty belongs to the defeated monster and is paid once.

    Prize: base_money * best_multiplier
    Notes: the payout doesn't depend on how many monsters joined the fight,
        nor on whether they survived it, so a mutual knockout still pays.
        Only the held items of the player's monsters that fought the loser
        count, and several holders apply the best multiplier rather than
        their product. Defeating one of the player's own monsters pays
        nothing.
    """

    name: ClassVar[MoneyMethod] = MoneyMethod.CONSERVED

    def calculate(
        self, loser: Monster, participants: Iterable[Monster]
    ) -> int:
        if loser.owner and loser.owner.is_player:
            return 0

        multipliers = [
            (
                participant.held_item.money_multiplier
                if participant.held_item
                else 1.0
            )
            for participant in participants
            if participant.owner and participant.owner.is_player
        ]

        if not multipliers:
            return 0

        base_money = calculate_money_base(loser.level, loser.money_modifier)

        return int(base_money * max(multipliers))


STRATEGY_MAP: dict[MoneyMethod, MoneyStrategy] = {
    MoneyMethod.PARTICIPANT_SCALED: ParticipantScaledMoneyStrategy(),
    MoneyMethod.CONSERVED: ConservedMoneyStrategy(),
}


def get_money_method(session: Session) -> MoneyMethod:
    """
    Return the money method of the campaign in play.

    A campaign chooses one by setting the game variable when it starts,
    which keeps the choice in the save. Campaigns that don't choose, and
    games saved before a campaign chose, use the default.
    """
    raw = session.player.game_variables.get(MONEY_METHOD_VARIABLE)
    try:
        return MoneyMethod(raw)
    except ValueError:
        logger.debug(
            f"No valid '{MONEY_METHOD_VARIABLE}' set ({raw!r}), "
            f"using {DEFAULT_MONEY_METHOD.value}"
        )
        return DEFAULT_MONEY_METHOD


def calculate_money(
    loser: Monster,
    participants: Iterable[Monster],
    method: MoneyMethod = DEFAULT_MONEY_METHOD,
) -> int:
    """Main entry point for prize money calculation."""
    strategy = STRATEGY_MAP.get(method, STRATEGY_MAP[DEFAULT_MONEY_METHOD])
    return strategy.calculate(loser, participants)
