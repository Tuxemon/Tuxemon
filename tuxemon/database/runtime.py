# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.database.bootstrap import bootstrap_database
from tuxemon.database.registry import validator

db = bootstrap_database()


def reset_runtime() -> None:
    """
    Reset the runtime for tests.
    Reinitializes both the validator and the database.
    """
    validator.reset()
    global db
    db = bootstrap_database()
