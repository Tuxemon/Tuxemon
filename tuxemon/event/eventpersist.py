# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class EventPersist:
    """Handles event persistence data, ensuring proper state tracking."""

    def __init__(self) -> None:
        self.storage: dict[str, dict[str, Any]] = defaultdict(dict)

    def update_event_data(self, event_name: str, key: str, value: Any) -> None:
        self.storage[event_name][key] = value

    def get_event_data(self, event_name: str) -> dict[str, Any]:
        return self.storage[event_name]
