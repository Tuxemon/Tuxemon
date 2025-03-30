# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Do not import platform-specific libraries such as pygame.
Graphics/audio operations should go to their own modules.

As the game library is developed and matures, move these into larger modules
if more appropriate.  Ideally this should be kept small.

"""

from __future__ import annotations

import logging
import typing
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import fields
from operator import add, eq, floordiv, ge, gt, le, lt, mul, ne, sub
from typing import (
    TYPE_CHECKING,
    Any,
    NoReturn,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from tuxemon import prepare
from tuxemon.compat.rect import ReadOnlyRect
from tuxemon.db import Comparison
from tuxemon.locale import T, replace_text
from tuxemon.math import Vector2

if TYPE_CHECKING:
    import pygame

    from tuxemon.item.item import Item
    from tuxemon.session import Session
    from tuxemon.sprite import Sprite
    from tuxemon.state import State


logger = logging.getLogger(__name__)

# Used to indicate that a function should never be called
# https://typing.readthedocs.io/en/latest/source/unreachable.html
Never = NoReturn

TVar = TypeVar("TVar")
TVarSequence = TypeVar("TVarSequence", bound=tuple[int, ...])

ValidParameterSingleType = Optional[type[Any]]
ValidParameterTypes = Union[
    ValidParameterSingleType,
    Sequence[ValidParameterSingleType],
]

ops_dict: Mapping[str, Callable[[float, float], int]] = {
    "+": add,
    "-": sub,
    "*": mul,
    "/": floordiv,
}


class NamedTupleProtocol(Protocol):
    """Protocol for arbitrary NamedTuple objects."""

    @property
    def _fields(self) -> tuple[str, ...]:
        pass


NamedTupleTypeVar = TypeVar("NamedTupleTypeVar", bound=NamedTupleProtocol)


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
    return prepare.fetch(*filename)


def scale_sequence(sequence: TVarSequence) -> TVarSequence:
    """
    Scale a sequence of integers by the configured scale factor.

    Parameters:
        sequence: Sequence to scale.

    Returns:
        Scaled sequence.

    """
    return type(sequence)(i * prepare.SCALE for i in sequence)


def scale(number: int) -> int:
    """
    Scale an integer by the configured scale factor.

    Parameter:
        number: Integer to scale.

    Returns:
        Scaled integer.

    """
    return prepare.SCALE * number


def calc_dialog_rect(
    screen_rect: pygame.rect.Rect, position: str
) -> pygame.rect.Rect:
    """
    Return a rect that is the area for a dialog box on the screen.

    Note:
        This only works with Pygame rects, as it modifies the attributes.

    Parameters:
        screen_rect: Rectangle of the screen.
        position: Position of the dialog box. Can be 'top', 'bottom', 'center',
            'topleft', 'topright', 'bottomleft', 'bottomright', 'right', 'left'.

    Returns:
        Rectangle for a dialog.
    """
    rect = screen_rect.copy()
    if prepare.CONFIG.large_gui:
        rect.height = int(rect.height * 0.4)
    else:
        rect.height = int(rect.height * 0.25)
        rect.width = int(rect.width * 0.8)

    if position == "top":
        rect.top = screen_rect.top
        rect.centerx = screen_rect.centerx
    elif position == "bottom":
        rect.bottom = screen_rect.bottom
        rect.centerx = screen_rect.centerx
    elif position == "center":
        rect.center = screen_rect.center
    elif position == "topleft":
        rect.topleft = screen_rect.topleft
    elif position == "topright":
        rect.topright = screen_rect.topright
    elif position == "bottomleft":
        rect.bottomleft = screen_rect.bottomleft
    elif position == "bottomright":
        rect.bottomright = screen_rect.bottomright
    elif position == "left":
        rect.left = screen_rect.left
        rect.centery = screen_rect.centery
    elif position == "right":
        rect.right = screen_rect.right
        rect.centery = screen_rect.centery
    else:
        raise ValueError("Invalid position.")

    return rect


def open_dialog(
    session: Session,
    text: Sequence[str],
    avatar: Optional[Sprite] = None,
    colors: dict[str, Any] = {},
    position: str = "bottom",
) -> State:
    """
    Open a dialog with the standard window size.

    Parameters:
        session: Game session.
        text: List of strings.
        avatar: Optional avatar sprite.
        colors: Dictionary containing background color, font color, etc.
        position: Position of the dialog box. Can be 'top', 'bottom', 'center',
            'topleft', 'topright', 'bottomleft', 'bottomright'.

    Returns:
        The pushed dialog state.

    """
    from tuxemon.states.dialog import DialogState

    rect = calc_dialog_rect(session.client.screen.get_rect(), position)
    return session.client.push_state(
        DialogState(
            text=text,
            avatar=avatar,
            rect=rect,
            colors=colors,
        )
    )


def open_choice_dialog(
    session: Session,
    menu: Sequence[tuple[str, str, Callable[[], None]]],
    escape_key_exits: bool = False,
) -> State:
    """
    Open a dialog choice with the standard window size.

    Parameters:
        session: Game session.
        menu: Optional menu object.

    Returns:
        The pushed dialog choice state.

    """
    from tuxemon.states.choice.choice_state import ChoiceState

    return session.client.push_state(
        ChoiceState(
            menu=menu,
            escape_key_exits=escape_key_exits,
        )
    )


def vector2_to_tile_pos(vector: Vector2) -> tuple[int, int]:
    return (int(vector[0]), int(vector[1]))


def number_or_variable(
    session: Session,
    value: str,
) -> float:
    """
    Returns a numeric game variable by its name.

    If ``value`` is already a number, convert from string to float and
    return that.

    Parameters:
        session: Session object, that contains the requested variable.
        value: Name of the requested variable or string with numerical value.

    Returns:
        Numerical value contained in the string or in the variable referenced
        by that name.

    Raises:
        ValueError: If ``value`` is not a number but no numeric variable with
        that name can be retrieved.

    """
    player = session.player
    if value.isdigit():
        return float(value)
    elif value.replace(".", "", 1).isdigit():
        return float(value)
    else:
        try:
            return float(player.game_variables[value])
        except (KeyError, ValueError, TypeError):
            raise ValueError(f"invalid number or game variable {value}")


# TODO: stability/testing
def cast_value(
    i: tuple[tuple[ValidParameterTypes, str], Any],
) -> Any:
    (type_constructors, param_name), value = i

    # Normalize type constructors to a list
    if not isinstance(type_constructors, Sequence):
        type_constructors = [type_constructors]

    # Early return for None or empty string if None is in type constructors
    if value is None or value == "":
        if None in type_constructors or type(None) in type_constructors:
            return None

    # Check for numeric types first to avoid float > int or int > float
    numeric_constructors = [float, int]
    if any(_con in type_constructors for _con in numeric_constructors):
        for _cons in type_constructors:
            if _cons is None:
                return None
            elif type(value) == _cons:
                return value
        # If value is not already of a numeric type, try to cast it
        for _cons in numeric_constructors:
            if _cons in type_constructors:
                try:
                    return _cons(value)
                except (ValueError, TypeError):
                    pass

    # Try to cast value to each type constructor
    for constructor in type_constructors:
        if not constructor:
            continue

        if isinstance(value, constructor):
            return value

        elif typing.get_origin(constructor) is typing.Literal:
            allowed_values = typing.get_args(constructor)
            if value in allowed_values:
                return value

        else:
            try:
                return constructor(value)
            except (ValueError, TypeError):
                pass

    # If all attempts fail, raise a ValueError
    raise ValueError(
        f"Error parsing parameter {param_name} with value {value} and "
        f"constructor list {type_constructors}",
    )


def get_types_tuple(
    param_type: ValidParameterSingleType,
) -> Sequence[ValidParameterSingleType]:
    if typing.get_origin(param_type) is Union:
        return typing.get_args(param_type)
    # TODO remove # if Python v3.10 (now 3.9)
    # from types import UnionType
    # elif typing.get_origin(param_type) is UnionType:
    #    return typing.get_args(param_type)
    else:
        return (param_type,)


def cast_dataclass_parameters(self: Any) -> None:
    """
    Takes a dataclass object and casts its __init__ values to the correct type
    """
    type_hints = typing.get_type_hints(self.__class__)
    for field in fields(self):
        if field.init:
            field_name = field.name  # e.g "map_name"
            type_hint = type_hints[field_name]  # e.g. Optional[str]
            constructors = get_types_tuple(
                type_hint
            )  # e.g. (<class 'str'>, <class 'NoneType'>)
            old_value = getattr(self, field_name)
            new_value = cast_value(((constructors, field_name), old_value))
            setattr(self, field_name, new_value)


def show_item_result_as_dialog(
    session: Session,
    item: Item,
    result: bool,
) -> None:
    """
    Show generic dialog if item was used or not.

    Parameters:
        session: Game session.
        item: Item object.
        result: Boolean indicating success or failure.

    """
    msg_type = "use_success" if result else "use_failure"
    template = getattr(item, msg_type)
    if template:
        message = T.translate(replace_text(session, template))
        open_dialog(session, [message])


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


def compare(
    key: str, value1: Union[int, float], value2: Union[int, float]
) -> bool:
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
    if key == Comparison.less_than or key == "<":
        return bool(lt(value1, value2))
    elif key == Comparison.less_or_equal or key == "<=":
        return bool(le(value1, value2))
    elif key == Comparison.greater_than or key == ">":
        return bool(gt(value1, value2))
    elif key == Comparison.greater_or_equal or key == ">=":
        return bool(ge(value1, value2))
    elif key == Comparison.equals or key == "==":
        return bool(eq(value1, value2))
    elif key == Comparison.not_equals or key == "!=":
        return bool(ne(value1, value2))
    else:
        raise ValueError(f"{key} isn't among {list(Comparison)}")
