# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class CaptureDeviceEffect:
    target_attribute: str = ""
    operation: str = ""
    value: str | int = 1


@dataclass
class CaptureDeviceConfig:
    specific_capdev_modifier: float | None = None
    positive_modifier: float = 1.0
    negative_modifier: float = 1.2
    specific_status_modifiers: dict[str, float] | None = None
    fallback_element_malus: float = 0.2
    specific_element_modifiers: dict[str, float] | None = None
    fallback_gender_malus: float = 0.2
    specific_gender_modifiers: dict[str, float] | None = None
    fallback_variables_malus: float = 0.2
    fallback_variables_bonus: float = 1.5
    specific_variables_modifiers: list[dict[str, Any]] | None = None
    random_bounds: tuple[float, float] | None = None
    capdev_persistent_on_success: bool = False
    capdev_persistent_on_failure: bool = False
    capdev_effects: list[CaptureDeviceEffect] | None = None


@dataclass
class CaptureDevicesConfig:
    items: dict[str, CaptureDeviceConfig]
    status_modifier: float = 1.0
    capdev_modifier: float = 1.0


@dataclass
class StatWeight:
    stat: str
    weight: float


@dataclass
class RangeMapEntry:
    user_stat: StatWeight
    target_stat: StatWeight


@dataclass
class CaptureConfig:
    total_shakes: int
    shake_constant: int
    shake_denominator: int
    shake_divisor: int
    shake_hp_multiplier: int
    shake_current_hp_multiplier: int
    shake_hp_divisor: int


@dataclass
class MonsterConfig:
    starting_bond: int = 25
    max_moves: int = 4
    max_tps: int = 150
    max_total_tps: int = 300
    default_tp_gain: int = 1
    coeff_stats: int = 7
    bond_range: tuple[int, int] = (0, 100)
    iv_range: tuple[int, int] = (0, 31)
    level_range: tuple[int, int] = (0, 100)
    catch_rate_range: tuple[int, int] = (0, 100)
    catch_resistance_range: tuple[float, float] = (0.0, 2.0)
    weight_range: tuple[float, float] = (-0.1, 0.1)
    height_range: tuple[float, float] = (-0.1, 0.1)
    bond_modifiers: dict[str, int] = field(default_factory=dict)
    bond_sentiments: dict[str, tuple[int, int]] = field(default_factory=dict)
    bond_strings: dict[str, str] = field(default_factory=dict)
    bond_icons: dict[str, str] = field(default_factory=dict)
    bond_stage_floors: dict[str, int] = field(default_factory=dict)
    bond_acquisition: dict[str, int] = field(default_factory=dict)
    bond_milestones: list[int] = field(default_factory=list)
    opposite_tastes: dict[str, list[str]] = field(default_factory=dict)
    bond_preferences: dict[str, int] = field(default_factory=dict)
    experience_multipliers: dict[str, float] = field(default_factory=dict)
    experience_groups: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class CombatConfig:
    letter_time: float
    action_time: float
    multiplier_map: dict[float, str]
    multiplier_range: tuple[float, float]
    # speed test
    speed_factor: float
    speed_offset: float
    dodge_modifier: float
    base_speed_bonus: float
    min_speed_modifier: float
    sort_order: list[str]

    def validate_multiplier_map(self) -> None:
        min_range, max_range = self.multiplier_range
        for multiplier in self.multiplier_map.keys():
            if not (min_range <= multiplier <= max_range):
                raise ValueError(
                    f"Multiplier {multiplier} is outside the allowed range: {self.multiplier_range}"
                )


class Loader:
    _config_combat: CombatConfig | None = None
    _config_monster: MonsterConfig | None = None
    _config_capture: CaptureConfig | None = None
    _range_map: dict[str, RangeMapEntry] = {}
    _capture_devices: CaptureDevicesConfig | None = None

    @classmethod
    def get_capture_devices(cls, filename: str) -> CaptureDevicesConfig:
        yaml_path = paths.mods_folder / filename
        if cls._capture_devices is None:
            raw_map = load_yaml(yaml_path)
            items = {}

            for slug, data in raw_map["items"].items():
                # Parse capdev_effects directly as a list
                capdev_effects = None
                if "capdev_effects" in data:
                    capdev_effects = [
                        CaptureDeviceEffect(
                            target_attribute=effect["target_attribute"],
                            operation=effect["operation"],
                            value=effect["value"],
                        )
                        for effect in data["capdev_effects"]
                    ]

                # Create a new dictionary excluding "capdev_effects" to avoid duplication
                filtered_data = {
                    key: value
                    for key, value in data.items()
                    if key != "capdev_effects"
                }

                items[slug] = CaptureDeviceConfig(
                    **filtered_data,
                    capdev_effects=capdev_effects,
                )

            # Handle global settings
            status_modifier = raw_map.get("status_modifier", 1.0)
            capdev_modifier = raw_map.get("capdev_modifier", 1.0)
            cls._capture_devices = CaptureDevicesConfig(
                status_modifier=status_modifier,
                capdev_modifier=capdev_modifier,
                items=items,
            )
        return cls._capture_devices

    @classmethod
    def get_config_combat(cls, filename: str) -> CombatConfig:
        yaml_path = paths.mods_folder / filename
        if cls._config_combat is None:
            raw_map = load_yaml(yaml_path)
            cls._config_combat = CombatConfig(**raw_map)
        return cls._config_combat

    @classmethod
    def get_config_monster(cls, filename: str) -> MonsterConfig:
        yaml_path = paths.mods_folder / filename
        if cls._config_monster is None:
            raw_map = load_yaml(yaml_path)
            cls._config_monster = MonsterConfig(**raw_map)
        return cls._config_monster

    @classmethod
    def get_config_capture(cls, filename: str) -> CaptureConfig:
        yaml_path = paths.mods_folder / filename
        if cls._config_capture is None:
            raw_map = load_yaml(yaml_path)
            cls._config_capture = CaptureConfig(**raw_map)
        return cls._config_capture

    @classmethod
    def get_range_map(cls, filename: str) -> dict[str, RangeMapEntry]:
        yaml_path = paths.mods_folder / filename
        if not cls._range_map:
            raw_map = load_yaml(yaml_path)
            cls._range_map = {
                key: RangeMapEntry(
                    user_stat=StatWeight(
                        stat=item[0]["user_stat"], weight=item[0]["weight"]
                    ),
                    target_stat=StatWeight(
                        stat=item[1]["target_stat"], weight=item[1]["weight"]
                    ),
                )
                for key, item in raw_map.items()
            }
        return cls._range_map


config_combat = Loader.get_config_combat("config_combat.yaml")
config_monster = Loader.get_config_monster("config_monster.yaml")
config_capdev = Loader.get_capture_devices("capture_devices.yaml")
config_capture = Loader.get_config_capture("config_capture.yaml")
range_map = Loader.get_range_map("range_map.yaml")
