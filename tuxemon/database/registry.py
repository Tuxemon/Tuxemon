# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tuxemon.database.validator import Validator


class _ValidatorProxy:
    _instance: Validator | None = None
    _lock = Lock()

    def set(self, instance: Validator) -> None:
        with self._lock:
            if self._instance is not None:
                raise RuntimeError(
                    "Validator already initialized; cannot reinitialize."
                )
            self._instance = instance

    def reset(self) -> None:
        """Allow tests to clear the validator."""
        with self._lock:
            self._instance = None

    def __getattr__(self, name: Any) -> Any:
        if self._instance is None:
            raise RuntimeError(
                "Validator not initialized. Call bootstrap_database() first."
            )
        return getattr(self._instance, name)


validator = _ValidatorProxy()
