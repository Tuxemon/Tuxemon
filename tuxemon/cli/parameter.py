from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Parameter:
    """
    Used to categorize and manage parameters for commands

    """

    name: str
    klass: str
