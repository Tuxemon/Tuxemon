# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Do not import platform-specific libraries such as pygame.
Graphics/audio operations should go to their own modules.

As the game library is developed and matures, move these into larger modules
if more appropriate.  Ideally this should be kept small.

"""

from __future__ import annotations

import logging
import typing
from dataclasses import fields
from itertools import zip_longest
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Mapping,
    NoReturn,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from tuxemon import prepare
from tuxemon.compat import ReadOnlyRect
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
TVarSequence = TypeVar("TVarSequence", bound=Tuple[int, ...])

ValidParameterSingleType = Optional[Type[Any]]
ValidParameterTypes = Union[
    ValidParameterSingleType,
    Sequence[ValidParameterSingleType],
]


class NamedTupleProtocol(Protocol):
    """Protocol for arbitrary NamedTuple objects."""

    @property
    def _fields(self) -> Tuple[str, ...]:
        pass


NamedTupleTypeVar = TypeVar("NamedTupleTypeVar", bound=NamedTupleProtocol)


def get_cell_coordinates(
    rect: ReadOnlyRect,
    point: Tuple[int, int],
    size: Tuple[int, int],
) -> Tuple[int, int]:
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


def calc_dialog_rect(screen_rect: pygame.rect.Rect) -> pygame.rect.Rect:
    """
    Return a rect that is the area for a dialog box on the screen.

    Note:
        This only works with Pygame rects, as it modifies the attributes.

    Parameters:
        screen_rect: Rectangle of the screen.

    Returns:
        Rectangle for a dialog.

    """
    rect = screen_rect.copy()
    if prepare.CONFIG.large_gui:
        rect.height *= 4
        rect.height //= 10
        rect.bottomleft = screen_rect.bottomleft
    else:
        rect.height //= 4
        rect.width *= 8
        rect.width //= 10
        rect.center = screen_rect.centerx, screen_rect.bottom - rect.height
    return rect


def open_dialog(
    session: Session,
    text: Sequence[str],
    avatar: Optional[Sprite] = None,
    menu: Optional[Tuple[str, str, Callable[[], None]]] = None,
) -> State:
    """
    Open a dialog with the standard window size.

    Parameters:
        session: Game session.
        text: List of strings.
        avatar: Optional avatar sprite.
        menu: Optional menu object.

    Returns:
        The pushed dialog state.

    """
    from tuxemon.states.dialog import DialogState

    rect = calc_dialog_rect(session.client.screen.get_rect())
    return session.client.push_state(
        DialogState(
            text=text,
            avatar=avatar,
            rect=rect,
            menu=menu,
        )
    )


def open_choice_dialog(
    session: Session,
    menu: Sequence[Tuple[str, str, Callable[[], None]]],
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
    from tuxemon.states.choice import ChoiceState

    return session.client.push_state(
        ChoiceState(
            menu=menu,
            escape_key_exits=escape_key_exits,
        )
    )


def vector2_to_tile_pos(vector: Vector2) -> Tuple[int, int]:
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
    else:
        try:
            return float(player.game_variables[value])
        except (KeyError, ValueError, TypeError):
            raise ValueError(f"invalid number or game variable {value}")


# TODO: stability/testing
def cast_value(
    i: Tuple[Tuple[ValidParameterTypes, str], Any],
) -> Any:

    (type_constructors, param_name), value = i

    if not isinstance(type_constructors, Sequence):
        type_constructors = [type_constructors]

    if (value is None or value == "") and (
        None in type_constructors or type(None) in type_constructors
    ):
        return None

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

    raise ValueError(
        f"Error parsing parameter {param_name} with value {value} and "
        f"constructor list {type_constructors}",
    )


def cast_values(
    parameters: Sequence[Any],
    valid_parameters: Sequence[Tuple[ValidParameterTypes, str]],
) -> Sequence[Any]:
    """
    Change all the string values to the expected type.

    This will also check and enforce the correct parameters for actions.

    Parameters:
        parameters: Parameters passed to the scripted object.
        valid_parameters: Allowed parameters and their types.

    Returns:
        Parameters converted to their correct type.

    """

    try:
        return list(map(cast_value, zip_longest(valid_parameters, parameters)))
    except ValueError:
        logger.warning("Invalid parameters passed:")
        logger.warning(f"expected: {valid_parameters}")
        logger.warning(f"got: {parameters}")
        raise


def get_types_tuple(
    param_type: ValidParameterSingleType,
) -> Sequence[ValidParameterSingleType]:
    if typing.get_origin(param_type) is Union:
        return typing.get_args(param_type)
    else:
        return (param_type,)


def cast_dataclass_parameters(self):
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


def cast_parameters_to_namedtuple(
    parameters: Sequence[Any],
    namedtuple_class: Type[NamedTupleTypeVar],
) -> NamedTupleTypeVar:
    valid_parameters = [
        (get_types_tuple(typing.get_type_hints(namedtuple_class)[f]), f)
        for f in namedtuple_class._fields
    ]

    values = cast_values(parameters, valid_parameters)
    return namedtuple_class(*values)


def show_item_result_as_dialog(
    session: Session,
    item: Item,
    result: Mapping[str, Any],
) -> None:
    """
    Show generic dialog if item was used or not.

    Parameters:
        session: Game session.
        item: Item object.
        result: A dict with a ``success`` key indicating sucess or failure.

    """
    msg_type = "use_success" if result["success"] else "use_failure"
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
