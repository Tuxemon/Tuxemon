# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from tuxemon.startup_rules import StartupRule

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.config import TuxemonConfig


class MyStartupRule(StartupRule):
    name: ClassVar[str] = "MyStartupRule"

    def __init__(
        self,
        client: LocalPygameClient,
        config: TuxemonConfig,
        load_slot: int | None = None,
    ):
        self.client = client
        self.config = config
        self.load_slot = load_slot

    def should_apply(self) -> bool:
        return True

    def apply(self) -> None:
        pass
