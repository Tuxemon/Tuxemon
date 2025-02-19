# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Parameter:
    """
    Used to categorize and manage parameters for commands.

    """

    name: str
