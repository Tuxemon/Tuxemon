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

    The status currently on the monster is responsible for the reaction: its
    ``on_positive_status`` / ``on_negative_status`` fields are read
    according to the category of the incoming status. A field left unset
    means the current status is sticky for that category, so the incoming
    status is blocked.
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

        # Category-based transitions: the status already on the monster
        # decides how it reacts to the category of the incoming status.
        # Uncategorised statuses (eg faint) are bookkeeping and always land.
        if new.category == CategoryStatus.POSITIVE:
            outcome = current.on_positive_status or ResponseStatus.BLOCKED
        elif new.category == CategoryStatus.NEGATIVE:
            outcome = current.on_negative_status or ResponseStatus.BLOCKED
        else:
            outcome = ResponseStatus.REPLACED

        # Map outcome to reason
        # ALREADY_PRESENT is reserved for re-applying the very same status
        # (handled above), so a different status being absorbed by the
        # current one is reported as having had no effect.
        reason_map = {
            ResponseStatus.REPLACED: BlockedReason.REPLACED,
            ResponseStatus.REMOVED: BlockedReason.REMOVED,
            ResponseStatus.STACKED: BlockedReason.ALREADY_PRESENT,
            ResponseStatus.BLOCKED: BlockedReason.NO_EFFECT,
        }

        return TransitionResult(
            outcome=outcome,
            reason=reason_map.get(outcome, BlockedReason.NO_EFFECT),
            replaced_status=current,
        )
