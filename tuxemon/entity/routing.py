# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from tuxemon.constants.paths import mods_folder
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.platform.const.sizes import KENNEL, LOCKER

if TYPE_CHECKING:
    from tuxemon.save_system.save_state import NPCState

logger = logging.getLogger(__name__)


class RoutingPolicyRegistry:
    _policies: dict[str, dict[str, Any]] = {}

    @classmethod
    def load_from_file(cls, path: str = "routing_policies.yaml") -> None:
        yaml_path = mods_folder / path
        raw = load_yaml(yaml_path)
        cls._policies = raw

    @classmethod
    def get(cls, name: str) -> RoutingPolicy:
        if not cls._policies:
            cls.load_from_file()
        if name not in cls._policies:
            raise KeyError(f"Routing policy '{name}' not found.")
        return RoutingPolicy.from_registry(name)

    @classmethod
    def get_raw(cls, name: str) -> dict[str, Any]:
        if not cls._policies:
            cls.load_from_file()
        return cls._policies[name]

    @classmethod
    def has(cls, name: str) -> bool:
        if not cls._policies:
            cls.load_from_file()
        return name in cls._policies


@dataclass
class RoutingPolicy:
    name: str
    force_to_box: bool = False
    kennel_override: str | None = None
    locker_override: str | None = None
    max_party_size: int | None = None
    allow_party_addition: bool = True
    auto_release_if_box_full: bool = False
    auto_discard_if_box_full: bool = False
    overflow_kennel: str | None = None
    overflow_locker: str | None = None
    max_box_capacity: int | None = None
    nickname_rules: dict[str, Any] = field(default_factory=dict)
    kennel_name_rules: dict[str, Any] = field(default_factory=dict)
    locker_name_rules: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_registry(cls, name: str) -> RoutingPolicy:
        raw = RoutingPolicyRegistry.get_raw(name)
        return cls(
            name=name,
            force_to_box=bool(raw.get("force_to_box", False)),
            kennel_override=raw.get("kennel_override"),
            locker_override=raw.get("locker_override"),
            max_party_size=raw.get("max_party_size"),
            allow_party_addition=bool(raw.get("allow_party_addition", True)),
            auto_release_if_box_full=bool(
                raw.get("auto_release_if_box_full", False)
            ),
            auto_discard_if_box_full=bool(
                raw.get("auto_discard_if_box_full", False)
            ),
            overflow_kennel=raw.get("overflow_kennel"),
            overflow_locker=raw.get("overflow_locker"),
            max_box_capacity=raw.get("max_box_capacity"),
            nickname_rules=raw.get("nickname_rules", {}),
            kennel_name_rules=raw.get("kennel_name_rules", {}),
            locker_name_rules=raw.get("locker_name_rules", {}),
        )

    def should_force_to_box(self) -> bool:
        return self.force_to_box

    def get_kennel(self) -> str:
        return self.kennel_override or KENNEL

    def get_locker(self) -> str:
        return self.locker_override or LOCKER

    def serialize(self) -> str:
        return self.name

    @classmethod
    def deserialize(cls, data: NPCState) -> str:
        name = data.routing_policy

        if not isinstance(name, str) or not name:
            logger.warning(
                "No routing policy found in save data. Falling back to 'default'."
            )
            return "default"

        if not RoutingPolicyRegistry.has(name):
            logger.warning(
                f"Routing policy '{name}' not found in registry. Falling back to 'default'."
            )
            return "default"

        return name
