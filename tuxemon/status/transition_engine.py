# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.db import BlockedReason, CategoryStatus, ResponseStatus

if TYPE_CHECKING:
    from tuxemon.status.status import Status


@dataclass
class TransitionResult:
    outcome: ResponseStatus
    reason: BlockedReason | None = None
    replaced_status: Status | None = None


class TransitionEngine:
    """
    Determines how a new status interacts with the current one.
    """

    def resolve(self, current: Status | None, new: Status) -> TransitionResult:

        # No current status → apply new one
        if current is None:
            return TransitionResult(
                outcome=ResponseStatus.REPLACED,
                reason=BlockedReason.REPLACED,
            )

        # Same status → stacking
        if current.slug == new.slug:
            return TransitionResult(
                outcome=ResponseStatus.STACKED,
                reason=BlockedReason.ALREADY_PRESENT,
                replaced_status=current,
            )

        # Category-based transitions
        if current.category == CategoryStatus.POSITIVE:
            outcome = new.on_positive_status or ResponseStatus.REPLACED
        elif current.category == CategoryStatus.NEGATIVE:
            outcome = new.on_negative_status or ResponseStatus.REPLACED
        else:
            outcome = ResponseStatus.REPLACED

        # Map outcome to reason
        reason_map = {
            ResponseStatus.REPLACED: BlockedReason.REPLACED,
            ResponseStatus.REMOVED: BlockedReason.REMOVED,
            ResponseStatus.STACKED: BlockedReason.ALREADY_PRESENT,
        }

        return TransitionResult(
            outcome=outcome,
            reason=reason_map.get(outcome, BlockedReason.NO_EFFECT),
            replaced_status=current,
        )
