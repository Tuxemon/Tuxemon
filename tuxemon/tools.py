# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Do not import platform-specific libraries such as pygame.
Graphics/audio operations should go to their own modules.

As the game library is developed and matures, move these into larger modules
if more appropriate.  Ideally this should be kept small.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import fields
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from functools import cache
from operator import add, eq, ge, gt, le, lt, mul, ne, sub
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NoReturn,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID

from tuxemon.compat.rect import ReadOnlyRect
from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.db import Comparison
from tuxemon.locale.locale import T
from tuxemon.scaling import ScalingStrategy
from tuxemon.ui.dialogue import calc_dialog_rect
from tuxemon.ui.text_alignment import DialogPosition
from tuxemon.ui.text_formatter import TextFormatter

if TYPE_CHECKING:
    from pygame.rect import Rect

    from tuxemon.base_client import BaseClient
    from tuxemon.game_variables import ScopeVariablesManager
    from tuxemon.item.item import Item
    from tuxemon.session import Session
    from tuxemon.sprite import Sprite
    from tuxemon.state.state import State
    from tuxemon.states.choice_state import MenuStateConfig
    from tuxemon.technique.technique import Technique
    from tuxemon.ui.menu_options import MenuOptions


logger = logging.getLogger(__name__)

# Used to indicate that a function should never be called
# https://typing.readthedocs.io/en/latest/source/unreachable.html
Never = NoReturn

TVar = TypeVar("TVar")


ValidParameterSingleType = type[Any] | None
ValidParameterTypes = (
    ValidParameterSingleType | Sequence[ValidParameterSingleType]
)


def safe_floordiv(a: float, b: float) -> int:
    if b == 0:
        return int(a)  # no-op fallback
    return int(a // b)


ops_dict: Mapping[str, Callable[[float, float], int]] = {
    "+": add,
    "-": sub,
    "*": mul,
    "/": safe_floordiv,
}


def get_cell_coordinates(
    rect: ReadOnlyRect,
    point: tuple[int, int],
    size: tuple[int, int],
) -> tuple[int, int]:
    """Find the cell of size, within rect, that point occupies."""
    point = (point[0] - rect.x, point[1] - rect.y)
    cell_x = (point[0] // size[0]) * size[0]
    cell_y = (point[1] // size[1]) * size[1]
    return (cell_x, cell_y)


def transform_resource_filename(*filename: str) -> str:
    """
    Appends the resource folder name to a filename.

    Parameters:
        filename: Relative path of a resource.

    Returns:
        The absolute path of the resource.
    """
    return fetch_asset(*filename)


def get_screen_rect(sprite: Sprite, internal_rect: Rect) -> Rect:
    """
    Converts a rectangle from HUD local coordinates to screen coordinates.

    Parameters:
        sprite: The HUD sprite whose position on screen defines the base.
        internal_rect: The Rect relative to sprite.image.

    Returns:
        A Rect object in screen coordinates.
    """
    return internal_rect.move(sprite.rect.topleft)


def scale(number: int, scaling: ScalingStrategy | None = None) -> int:
    """Scale a number by the configured scale factor."""
    if scaling is None:
        from tuxemon.prepare import DISPLAY_CONTEXT

        scaling = DISPLAY_CONTEXT.scaling

    return scaling.scale_int(number)


TEnum = TypeVar("TEnum", bound=Enum)


def safe_enum_value(
    enum_class: type[TEnum],
    value: str | None,
    default: TEnum,
    raise_on_error: bool = False,
) -> TEnum:
    """
    Attempts to convert a string to an enum member.
    Raises or falls back to default on failure.
    """
    try:
        return enum_class(value)
    except (ValueError, TypeError) as e:
        if raise_on_error:
            raise ValueError(
                f"Invalid value for {enum_class.__name__}: {value!r}"
            ) from e
        logger.warning(
            f"Invalid value for {enum_class.__name__}: {value!r}, using default: {default}"
        )
        return default


def get_valid_uuid(
    game_variables: ScopeVariablesManager, variable_name: str
) -> UUID | None:
    """Safely retrieves a valid UUID from game variables."""
    raw_value: str | None = game_variables.get(variable_name)

    if raw_value in ("no_choice", "no_options", None):
        logger.info(
            f"Monster selection result for '{variable_name}': {raw_value}"
        )
        return None

    try:
        return UUID(str(raw_value))
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Invalid UUID format for '{variable_name}': {raw_value} ({e})"
        )
        return None


def fix_measure(measure: int, percentage: float) -> int:
    """it returns the correct measure based on percentage"""
    return round(measure * percentage)


def open_dialog(
    client: BaseClient,
    text: Sequence[str],
    avatar: Sprite | None = None,
    box_style: dict[str, Any] | None = None,
    position: DialogPosition = DialogPosition.BOTTOM,
    target_coords: tuple[int, int] | Rect | None = None,
    custom_rect: Rect | None = None,
    on_complete: Callable[[], None] | None = None,
    dialog_speed: str | None = None,
) -> State:
    """
    Open a dialog with the standard window size or a custom size/position.

    Parameters:
        client: Game client.
        text: List of strings for the dialog content.
        avatar: Optional avatar sprite to display in the dialog.
        box_style: Dictionary containing background color, font color, etc.
        position: Position of the dialog box. Can be 'top', 'bottom', 'center',
            'topleft', 'topright', 'bottomleft', 'bottomright', 'right', 'left',
            or 'at_target' (if target_coords is a point).
            If target_coords is provided, this position will be relative to the target.
            Otherwise, it will be relative to the screen.
            This parameter is ignored if custom_rect is provided.
        target_coords: Optional. A tuple (x, y) representing a point, or a Pygame Rect.
            If provided, the 'position' will be relative to this point/rect.
            Ignored if custom_rect is provided.
        custom_rect: Optional. A Pygame Rect object specifying the exact area for the dialog.
            If provided, 'position' and 'target_coords' will be ignored.
        dialog_speed: Characters-per-frame delay for text rendering. If `None`, falls
            back to the client's configured default. Use 'slow' for instant text display.

    Returns:
        The pushed dialog state.
    """
    box_style = box_style or {}
    if custom_rect is not None:
        dialog_rect = custom_rect
    else:
        dialog_rect = calc_dialog_rect(
            client.context.rect, position, target_coords=target_coords
        )

    return client.push_state(
        "DialogState",
        rect=dialog_rect,
        text=text,
        avatar=avatar,
        box_style=box_style,
        on_complete=on_complete,
        dialog_speed=dialog_speed,
    )


def open_choice_dialog(
    client: BaseClient,
    menu: MenuOptions,
    escape_key_exits: bool = False,
    config: MenuStateConfig | None = None,
) -> State:
    """
    Opens a dialog choice using the standard window size.

    Parameters:
        client: The LocalPygameClient instance.
        menu: A MenuOptions instance.
        escape_key_exits: Whether pressing the escape key will close the
            dialog (default: False).
        config: Configuration for the menu.

    Returns:
        The newly pushed dialog choice state.
    """
    return client.push_state(
        "ChoiceState",
        menu=menu,
        escape_key_exits=escape_key_exits,
        config=config,
    )


def number_or_variable(variables: dict[str, Any], value: str) -> float:
    """
    Converts a string to a numeric value or retrieves a numeric variable by
    name.

    This function attempts to convert the input string `value` into a float.
    If that fails, it then tries to retrieve a variable by its name from the
    `variables` dictionary and convert its value to a float.

    Parameters:
        variables: A dictionary containing variable names and their
            corresponding values.
        value: Either a string containing a numeric value or the name of a
            variable.

    Returns:
        The numeric value obtained by converting the string or retrieving
        the variable.

    Raises:
        ValueError: If `value` is neither a valid numeric string nor a valid
        variable name, or the retrieved variable value cannot be converted to
        a float.
    """
    try:
        return float(value)
    except ValueError:
        try:
            return float(variables[value])
        except (KeyError, ValueError, TypeError):
            raise ValueError(
                f"Unable to retrieve numeric variable or convert value '{value}'."
            )


def cast_value(
    i: tuple[tuple[ValidParameterTypes, str], Any],
) -> Any:
    """
    Attempt to cast a raw value into one of the expected types.

    Parameters:
        i: A tuple containing ((constructors, param_name), value).
           - constructors: sequence of type constructors or typing hints
           - param_name: name of the parameter (for error messages)
           - value: the raw value to cast

    Returns:
        The value cast to one of the expected types.

    Raises:
        ValueError: if the value cannot be cast to any of the expected types.
    """
    (type_constructors, param_name), value = i

    # Normalize constructors into a list
    if not isinstance(type_constructors, Sequence) or isinstance(
        type_constructors, type
    ):
        type_constructors = [type_constructors]

    # Expand Union/Optional types
    expanded: list[Any] = []
    for c in type_constructors:
        if c is None:
            expanded.append(type(None))
        elif get_origin(c) == UnionType:
            expanded.extend(get_args(c))
        else:
            expanded.append(c)

    constructors_to_try: list[Any] = [c for c in expanded if c is not None]
    is_optional = type(None) in expanded

    # Handle None
    if value is None:
        if is_optional:
            return None
        raise ValueError(f"Parameter '{param_name}' cannot be None.")

    # Handle empty string
    if isinstance(value, str) and not value.strip():
        if is_optional:
            return None
        if str in constructors_to_try:
            return ""
        raise ValueError(f"Parameter '{param_name}' cannot be empty string.")

    # First pass: direct isinstance
    for constructor in constructors_to_try:
        if get_origin(constructor) is Literal:
            continue
        origin = get_origin(constructor) or constructor
        try:
            if isinstance(value, origin):
                return value
        except TypeError:
            continue

    # Special handling for numerics
    if any(c in constructors_to_try for c in (int, float, Decimal, Fraction)):
        try:
            if (
                int in constructors_to_try
                and isinstance(value, str)
                and value.isdigit()
            ):
                return int(value)
            if int in constructors_to_try:
                try:
                    return int(value)
                except ValueError:
                    # allow "3.0" → 3
                    if isinstance(value, str) and "." in value:
                        return int(float(value))
            if float in constructors_to_try:
                return float(value)
            if Decimal in constructors_to_try:
                return Decimal(value)
            if Fraction in constructors_to_try:
                return Fraction(value)
        except Exception:
            pass

    # Special handling for booleans
    if bool in constructors_to_try:
        if isinstance(value, str):
            val = value.strip().lower()
            if val in ("true", "1", "yes", "on"):
                return True
            if val in ("false", "0", "no", "off"):
                return False
            raise ValueError(
                f"Parameter '{param_name}' cannot be cast to bool from string '{value}'."
            )
        return bool(value)

    # Special handling for datetime/date/time/timedelta
    if datetime in constructors_to_try:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            pass
    if date in constructors_to_try:
        try:
            return date.fromisoformat(value)
        except Exception:
            pass
    if time in constructors_to_try:
        try:
            return time.fromisoformat(value)
        except Exception:
            pass
    if timedelta in constructors_to_try:
        try:
            return timedelta(seconds=float(value))
        except Exception:
            pass

    # Special handling for enums
    for constructor in constructors_to_try:
        if isinstance(constructor, type) and issubclass(constructor, Enum):
            if isinstance(value, constructor):
                return value
            try:
                return constructor(value)
            except Exception:
                pass

    # Handle Literal
    for constructor in constructors_to_try:
        if get_origin(constructor) is Literal:
            allowed_values = get_args(constructor)
            if value in allowed_values:
                return value
            raise ValueError(
                f"Parameter '{param_name}' must be one of {allowed_values}, got {value!r}"
            )

    # Handle collections (basic coercion)
    for constructor in constructors_to_try:
        origin = get_origin(constructor) or constructor
        if origin in (list, set, tuple):
            try:
                if isinstance(value, str):
                    parts = value.split(",")
                    if is_optional:
                        items = [
                            p.strip() if p.strip() else None for p in parts
                        ]
                    else:
                        items = [p.strip() for p in parts]
                    return origin(items)
                return origin(value)
            except Exception:
                pass
        elif origin is dict:
            try:
                if isinstance(value, str):
                    import json

                    return json.loads(value)
                return dict(value)
            except Exception:
                pass

    # Generic casting fallback
    for constructor in constructors_to_try:
        try:
            return constructor(value)
        except Exception:
            continue

    # If all attempts fail
    raise ValueError(
        f"Error parsing parameter '{param_name}': Cannot cast value {value!r} "
        f"(type {type(value).__name__}) to any of {constructors_to_try}"
    )


def get_types_tuple(
    param_type: ValidParameterSingleType,
) -> Sequence[ValidParameterSingleType]:
    """
    Expand a typing annotation into its component types.
    """
    origin = get_origin(param_type)

    if origin is UnionType:
        return get_args(param_type)

    if param_type is type(None):
        return (param_type,)

    return (param_type,)


@cache
def get_cached_type_info(cls: type) -> dict[str, tuple[type, ...]]:
    """
    Retrieve and cache type information for dataclass fields.
    """
    type_hints = get_type_hints(cls)

    info = {}
    for field in fields(cls):
        if not field.init:
            continue

        component_types: list[Any] = []
        for t in get_types_tuple(type_hints[field.name]):
            if isinstance(t, type):
                component_types.append(t)
            elif get_origin(t) is Literal:
                component_types.append(t)
            elif t is type(None):
                component_types.append(type(None))

        info[field.name] = tuple(component_types)

    return info


def cast_dataclass_parameters(obj: Any) -> None:
    """
    Cast all dataclass fields to their annotated types.

    Args:
        obj: The dataclass instance to mutate.

    Side effects:
        Mutates the dataclass instance in place.

    Raises:
        ValueError: if any field cannot be cast to its annotated type.
    """
    field_info = get_cached_type_info(obj.__class__)
    for field_name, constructors in field_info.items():
        old_value = getattr(obj, field_name)
        try:
            new_value = cast_value(((constructors, field_name), old_value))
        except ValueError as e:
            raise ValueError(
                f"Failed to cast field '{field_name}' with value {old_value!r}: {e}"
            ) from e
        setattr(obj, field_name, new_value)


def show_result_as_dialog(
    session: Session,
    entity: Item | Technique,
    result: bool,
) -> None:
    """
    Show generic dialog if item was used or not.

    Parameters:
        session: Game session.
        entity: Object (Item or Technique).
        result: Boolean indicating success or failure.
    """
    msg_type = "use_success" if result else "use_failure"
    template = getattr(entity, msg_type)
    if template:
        message = T.translate(TextFormatter.replace_text(session, template, T))
        open_dialog(session.client, [message])


def round_to_divisible(x: float, base: int = 16) -> int:
    """
    Rounds a number to a divisible base.

    This is used to round collision areas that aren't defined well. This
    function assists in making sure collisions work if the map creator didn't
    set the collision areas to round numbers.

    Parameters:
        x: The number we want to round.
        base: The base that we want our number to be divisible by. By default
            this is 16.

    Returns:
        Rounded number that is divisible by ``base``.
    """
    return int(base * round(float(x) / base))


def copy_dict_with_keys(
    source: Mapping[str, TVar],
    keys: Iterable[str],
) -> Mapping[str, TVar]:
    """
    Return new dict using only the keys/value from ``keys``.

    If key from keys is not present no error is raised.

    Parameters:
        source: Original mapping.
        keys: Allowed keys in the output mapping.

    Returns:
        New mapping with the keys restricted to those in ``keys``.
    """
    return {k: source[k] for k in keys if k in source}


def assert_never(value: Never) -> NoReturn:
    """
    Assertion for exhaustive checking of a variable.

    Parameters:
        value: The value that will be checked for exhaustiveness.
    """
    assert False, f"Unhandled value: {value} ({type(value).__name__})"


def compare(key: str, value1: int | float, value2: int | float) -> bool:
    """
    It compares and it returns a boleean whether is greater_than or not.

    It supports: less_than, less_or_equal, greater_than, greater_or_equal
        equals and not_equals.

    It supports: >, <, >=, <=, == and !=

    It raises a ValueError if the key isn't among the operators.

    Parameters:
        key: Key to check.
        value1: First value to compare.
        value2: Second value to compare.

    Returns:
        boolean: true / false
    """
    if key == Comparison.LESS_THAN or key == "<":
        return bool(lt(value1, value2))
    elif key == Comparison.LESS_OR_EQUAL or key == "<=":
        return bool(le(value1, value2))
    elif key == Comparison.GREATER_THAN or key == ">":
        return bool(gt(value1, value2))
    elif key == Comparison.GREATER_OR_EQUAL or key == ">=":
        return bool(ge(value1, value2))
    elif key == Comparison.EQUALS or key == "==":
        return bool(eq(value1, value2))
    elif key == Comparison.NOT_EQUALS or key == "!=":
        return bool(ne(value1, value2))
    else:
        raise ValueError(f"{key} isn't among {list(Comparison)}")


def compare_tuple(
    key: str,
    value1: tuple[int | float, int | float],
    value2: tuple[int | float, int | float],
) -> bool:
    """
    Tuple-based comparison using the same Comparison enum
    and symbolic operators supported by compare().
    """

    if key == Comparison.LESS_THAN or key == "<":
        return value1 < value2
    elif key == Comparison.LESS_OR_EQUAL or key == "<=":
        return value1 <= value2
    elif key == Comparison.GREATER_THAN or key == ">":
        return value1 > value2
    elif key == Comparison.GREATER_OR_EQUAL or key == ">=":
        return value1 >= value2
    elif key == Comparison.EQUALS or key == "==":
        return value1 == value2
    elif key == Comparison.NOT_EQUALS or key == "!=":
        return value1 != value2
    else:
        raise ValueError(f"{key} isn't among {list(Comparison)}")


def parse_flag(value: str | None) -> bool:
    """
    Convert a string flag to a boolean.

    Accepted truthy values: "true", "1", "yes" (case-insensitive).
    All other values (including None) return False.
    """
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def check_condition(value: str, dataset: set[str]) -> bool:
    """
    Check if a condition is satisfied against a set of values.

    - If the input starts with '!', it asserts that the value is NOT in the dataset.
    - Otherwise, it asserts that the value IS in the dataset.
    """
    value = value.strip().lower()
    if not value:
        logging.debug("Empty condition skipped.")
        return False

    if value.startswith("!"):
        result = value[1:] not in dataset
        logging.debug(f"Checking NOT '{value[1:]}' in {dataset}: {result}")
        return result

    result = value in dataset
    logging.debug(f"Checking '{value}' in {dataset}: {result}")
    return result


def format_playtime(seconds: float) -> str:
    """Convert seconds into a human-readable hours and minutes format."""
    minutes, sec = divmod(int(seconds), 60)
    hours, min = divmod(minutes, 60)
    return f"{hours}h {min}m"
