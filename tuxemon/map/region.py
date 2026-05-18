# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import TYPE_CHECKING, Any

from tuxemon.db import Direction
from tuxemon.platform.const.sizes import REGION_KEYS

if TYPE_CHECKING:
    from tuxemon.entity.entity import Entity

logger = logging.getLogger(__name__)

REGION_STRATEGIES: dict[RegionKey, type[RegionPropertiesStrategy]] = {}


class RegionKey(str, Enum):
    DEFAULT = "default"
    SLIDE = "slide"
    PUSH_TILE = "push_tile"


@dataclass(frozen=True)
class PushEffect:
    direction: Direction
    strength: int


@dataclass(frozen=True)
class RegionProperties:
    enter_from: Sequence[Direction] = field(
        default_factory=list,
        metadata={
            "description": "Directions from which an entity can enter this region."
        },
    )
    exit_from: Sequence[Direction] = field(
        default_factory=list,
        metadata={
            "description": "Directions from which an entity can exit this region."
        },
    )
    endure: Sequence[Direction] = field(
        default_factory=list,
        metadata={
            "description": "Directions from which an entity can remain in this region."
        },
    )
    entity: Entity | None = field(
        default=None,
        metadata={
            "description": "Optional entity associated with this region."
        },
    )
    key: str | None = field(
        default=None,
        metadata={
            "description": "Region behavior key (e.g., 'slide', 'push_tile')."
        },
    )
    push_effect: PushEffect | None = field(
        default=None,
        metadata={
            "description": "Push effect applied when entering this region."
        },
    )
    speed_modifier: float | None = field(
        default=None,
        metadata={
            "description": "Multiplier for movement speed within this region."
        },
    )

    def with_overrides(self, **kwargs: Any) -> RegionProperties:
        return replace(self, **kwargs)

    def __str__(self) -> str:
        return (
            f"RegionProperties(key={self.key}, enter={self.enter_from}, exit={self.exit_from}, "
            f"endure={self.endure}, push={self.push_effect}, speed={self.speed_modifier})"
        )


def register_region_strategy(
    key: RegionKey,
) -> Callable[
    [type[RegionPropertiesStrategy]], type[RegionPropertiesStrategy]
]:
    """
    Decorator to register a RegionPropertiesStrategy class with a specific RegionKey.
    """

    def decorator(
        cls: type[RegionPropertiesStrategy],
    ) -> type[RegionPropertiesStrategy]:
        if not issubclass(cls, RegionPropertiesStrategy):
            raise TypeError(
                f"Class {cls.__name__} must inherit from RegionPropertiesStrategy."
            )
        if key in REGION_STRATEGIES:
            logger.warning(
                f"Overwriting existing strategy for key '{key.value}' "
                f"({REGION_STRATEGIES[key].__name__} -> {cls.__name__})."
            )
        REGION_STRATEGIES[key] = cls
        return cls

    return decorator


class RegionPropertiesStrategy(ABC):
    """Abstract base class for all region property strategies."""

    @classmethod
    @abstractmethod
    def create(cls, parsed_data: dict[str, Any]) -> RegionProperties | None:
        pass


@register_region_strategy(RegionKey.DEFAULT)
class DefaultTileStrategy(RegionPropertiesStrategy):
    """
    Handles the default behavior for map regions,
    where directions are explicitly defined.
    """

    @classmethod
    def create(cls, parsed_data: dict[str, Any]) -> RegionProperties:
        return RegionProperties(
            enter_from=parsed_data.get("enter_from", []),
            exit_from=parsed_data.get("exit_from", []),
            endure=parsed_data.get("endure", []),
            entity=None,
            key=parsed_data.get("key"),
            push_effect=None,
            speed_modifier=parsed_data.get("speed_modifier"),
        )


@register_region_strategy(RegionKey.SLIDE)
class SlideTileStrategy(RegionPropertiesStrategy):
    """
    Handles the "slide" behavior, where all movements are allowed.
    """

    @classmethod
    def create(cls, parsed_data: dict[str, Any]) -> RegionProperties:
        all_dirs = list(Direction)
        return RegionProperties(
            enter_from=all_dirs,
            exit_from=all_dirs,
            endure=all_dirs,
            entity=None,
            key=RegionKey.SLIDE.value,
            push_effect=None,
            speed_modifier=parsed_data.get("speed_modifier"),
        )


@register_region_strategy(RegionKey.PUSH_TILE)
class PushTileStrategy(RegionPropertiesStrategy):
    """
    Handles the "push_tile" behavior, applying a push effect
    in a specific direction.
    """

    @classmethod
    def create(cls, parsed_data: dict[str, Any]) -> RegionProperties:
        push_direction = parsed_data.get("push_direction")
        push_strength = parsed_data.get("push_strength", 0)

        if push_direction is None or push_strength <= 0:
            raise ValueError(
                "'push_tile' key requires both 'push_direction' and a positive 'push_strength'."
            )

        all_dirs = list(Direction)
        enter_from = parsed_data.get("enter_from") or all_dirs
        exit_from = parsed_data.get("exit_from") or all_dirs

        return RegionProperties(
            enter_from=enter_from,
            exit_from=exit_from,
            endure=parsed_data.get("endure", []),
            entity=None,
            key=RegionKey.PUSH_TILE.value,
            push_effect=PushEffect(push_direction, push_strength),
            speed_modifier=parsed_data.get("speed_modifier"),
        )


def _parse_raw_properties(
    properties: Mapping[str, str | None],
) -> dict[str, Any] | None:
    if not properties:
        return None

    keys_lower = {k.lower() for k in properties}
    if not keys_lower & set(REGION_KEYS):
        return None

    parsed_data: dict[str, Any] = {
        "enter_from": [],
        "exit_from": [],
        "endure": [],
        "key": None,
        "push_direction": None,
        "push_strength": 0,
        "speed_modifier": None,
    }

    for key, value in properties.items():
        k = key.lower()
        if k in ["enter_from", "exit_from", "endure"]:
            if value == "":
                raise ValueError(
                    f"Invalid value for '{k}': cannot be an empty string"
                )
            parsed_data[k] = direction_to_list(value)
        elif k == "key":
            if not value:
                raise ValueError("Invalid value for 'key': cannot be empty")
            parsed_data["key"] = value.strip().lower()
        elif k == "push_direction":
            parsed_data["push_direction"] = direction_to_single(value)
        elif k == "push_strength":
            if value:
                try:
                    parsed_data["push_strength"] = int(value)
                except ValueError:
                    raise ValueError(
                        f"Invalid push_strength '{value}': must be an integer."
                    )
        elif k == "speed_modifier":
            if value:
                try:
                    parsed_data["speed_modifier"] = float(value)
                except ValueError:
                    raise ValueError(
                        f"Invalid speed_modifier '{value}': must be a number."
                    )
        # Optional: collect unknown keys for logging/debugging

    if parsed_data["exit_from"] and not parsed_data["enter_from"]:
        all_dirs = list(Direction)
        parsed_data["enter_from"] = sorted(
            set(all_dirs) - set(parsed_data["exit_from"]),
            key=lambda d: all_dirs.index(d),
        )

    return parsed_data


def create_region_properties(
    parsed_data: dict[str, Any],
) -> RegionProperties | None:
    key_str = (parsed_data.get("key") or "").lower()
    try:
        key = RegionKey(key_str)
    except ValueError:
        key = RegionKey.DEFAULT

    strategy_cls = REGION_STRATEGIES.get(key, DefaultTileStrategy)

    # Note: If DefaultTileStrategy is registered, this fallback is technically
    # redundant but harmless, and ensures a clean failure if someone deletes the
    # default registration.

    return strategy_cls.create(parsed_data)


def extract_region_properties(
    properties: Mapping[str, str | None],
) -> RegionProperties | None:
    """
    Given a dictionary from Tiled properties, return a dictionary
    suitable for collision detection.

    The function expects the input dictionary to contain keys from the following set:
    {"enter_from", "exit_from", "endure", "key"}. The values for "enter_from", "exit_from",
    and "endure" should be strings representing directions, while the value for "key"
    should be a string representing a label.

    If the input dictionary contains an "exit_from" key but no "enter_from" key, the
    function will automatically calculate the "enter_from" directions based on the
    "exit_from" directions.

    If the input dictionary contains a "key" with the value "slide", the function will
    set all movement directions to all possible directions.

    Parameters:
        properties: A dictionary from Tiled properties.

    Returns:
        A RegionProperties NamedTuple suitable for collision detection.

    Raises:
        ValueError: If the input dictionary contains an invalid value.
    """
    parsed = _parse_raw_properties(properties)
    if not parsed:
        return None

    region = create_region_properties(parsed)
    if region is None:
        logger.debug(
            f"Region creation returned None for parsed data: {parsed}"
        )
        return None

    return region


def direction_to_list(direction: str | None) -> list[Direction]:
    if direction is None:
        return []

    cleaned = direction.strip()
    if not cleaned:
        raise ValueError("Direction string is empty or whitespace.")

    try:
        return sorted(
            [
                Direction(d)
                for d in {d.strip().lower() for d in cleaned.split(",")}
            ]
        )
    except ValueError as e:
        raise ValueError(f"Invalid direction list: {direction}") from e


def direction_to_single(direction: str | None) -> Direction | None:
    if direction is None:
        return None

    cleaned = direction.strip()
    if not cleaned:
        raise ValueError("Direction string is empty or whitespace.")

    try:
        return Direction(cleaned.lower())
    except ValueError as e:
        raise ValueError(f"Invalid direction: {direction}") from e
