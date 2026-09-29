# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from tuxemon.database.runtime import db

if TYPE_CHECKING:
    from tuxemon.client import LocalPygameClient
    from tuxemon.config import TuxemonConfig


class StartupRule(ABC):
    name: ClassVar[str]

    @abstractmethod
    def should_apply(self) -> bool: ...

    @abstractmethod
    def apply(self) -> None: ...


def load_mod_startup_rules(
    client: LocalPygameClient,
    config: TuxemonConfig,
    load_slot: int | None = None,
) -> list[Any]:
    rules = []

    for mod_name in config.mods:
        meta = db.mod_metadata.get_mod_metadata(mod_name)
        rule_paths = meta.startup_rules

        for path in rule_paths:
            module_name, class_name = path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            rule = cls(client=client, config=config, load_slot=load_slot)
            rules.append(rule)

    return rules
