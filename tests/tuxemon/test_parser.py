# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.script.parser import (
    parse_action_string,
    parse_behav_string,
    parse_condition_string,
    split_escaped,
)


@pytest.mark.parametrize(
    "input_str, expected",
    [
        pytest.param("spam", ["spam"], id="single"),
        pytest.param("spam ", ["spam"], id="trailing_space"),
        pytest.param(" spam", ["spam"], id="leading_space"),
        pytest.param(" spam ", ["spam"], id="both_spaces"),
        pytest.param("spam , eggs  ", ["spam", "eggs"], id="two_items"),
        pytest.param(
            "spam , eggs,", ["spam", "eggs", ""], id="ends_with_comma"
        ),
        pytest.param(
            "spam , eggs  ,, ", ["spam", "eggs", "", ""], id="double_empty"
        ),
        pytest.param("", [], id="empty"),
        pytest.param(",", ["", ""], id="just_comma"),
        pytest.param(
            "spam\\,eggs,ham", ["spam,eggs", "ham"], id="escaped_comma"
        ),
        pytest.param("spam\\,eggs\\,ham", ["spam,eggs,ham"], id="escaped_two"),
    ],
)
def test_split_escaped(input_str, expected):
    assert split_escaped(input_str) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("spam", ("spam", []), id="single"),
        pytest.param("spam eggs", ("spam", ["eggs"]), id="one_arg"),
        pytest.param(
            "spam eggs,parrot", ("spam", ["eggs", "parrot"]), id="two_args"
        ),
        pytest.param("spam , ", ("spam", ["", ""]), id="empty_args"),
        pytest.param(
            "spam eggs, ", ("spam", ["eggs", ""]), id="trailing_empty"
        ),
        pytest.param("spam,eggs", ("spam,eggs", []), id="comma_in_type"),
        pytest.param("   spam   ", ("", ["spam"]), id="leading_spaces"),
        pytest.param("spam ,,", ("spam", ["", "", ""]), id="double_empty"),
        pytest.param(
            "spam ex parrot", ("spam", ["ex parrot"]), id="space_arg"
        ),
        pytest.param(
            "spam eggs,  ex parrot",
            ("spam", ["eggs", "ex parrot"]),
            id="mixed",
        ),
    ],
)
def test_parse_action_string(text, expected):
    assert parse_action_string(text) == expected


def test_no_type():
    with pytest.raises(ValueError):
        parse_condition_string("spam")


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("spam eggs", ("spam", "eggs", []), id="basic"),
        pytest.param(
            " spam eggs ", ("", "spam", ["eggs"]), id="leading_spaces"
        ),
        pytest.param(
            "spam eggs, ", ("spam", "eggs,", []), id="comma_after_type"
        ),
        pytest.param(
            "spam eggs, parrot", ("spam", "eggs,", ["parrot"]), id="one_arg"
        ),
        pytest.param(
            " spam eggs parrot, cheese, ",
            ("", "spam", ["eggs parrot", "cheese", ""]),
            id="multi_args",
        ),
        pytest.param(
            "spam eggs  ex parrot, cheese shop",
            ("spam", "eggs", ["ex parrot", "cheese shop"]),
            id="spaces_and_args",
        ),
    ],
)
def test_parse_condition_string(text, expected):
    assert parse_condition_string(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("walk", ("walk", []), id="walk"),
        pytest.param("walk north", ("walk", ["north"]), id="walk_arg"),
        pytest.param(
            "move npc1, npc2", ("move", ["npc1", "npc2"]), id="two_args"
        ),
        pytest.param(
            "  animate  idle  ", ("", ["animate  idle"]), id="spaces"
        ),
        pytest.param(
            "trigger a\\,b,c", ("trigger", ["a,b", "c"]), id="escaped_one"
        ),
        pytest.param(
            "trigger a\\,b\\,c", ("trigger", ["a,b,c"]), id="escaped_two"
        ),
    ],
)
def test_parse_behav_string(text, expected):
    assert parse_behav_string(text) == expected


def reconstruct_action(act_type: str, args: list[str]) -> str:
    if not args:
        return act_type
    escaped = [a.replace(",", r"\,") for a in args]
    return f"{act_type} " + ", ".join(escaped)


def reconstruct_condition(
    operator: str, cond_type: str, args: list[str]
) -> str:
    if not args:
        return f"{operator} {cond_type}"
    escaped = [a.replace(",", r"\,") for a in args]
    return f"{operator} {cond_type} " + ", ".join(escaped)


def reconstruct_behav(behav_type: str, args: list[str]) -> str:
    if not args:
        return behav_type
    escaped = [a.replace(",", r"\,") for a in args]
    return f"{behav_type} " + ", ".join(escaped)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("walk", id="walk"),
        pytest.param("walk north", id="walk_arg"),
        pytest.param("move npc1, npc2", id="two_args"),
        pytest.param("trigger a\\,b,c", id="escaped_one"),
        pytest.param("trigger a\\,b\\,c", id="escaped_two"),
        pytest.param("  animate idle  ", id="spaces"),
    ],
)
def test_roundtrip_behav(text):
    behav_type, args = parse_behav_string(text)
    reconstructed = reconstruct_behav(behav_type, args)
    behav_type2, args2 = parse_behav_string(reconstructed)
    assert behav_type == behav_type2
    assert args == args2


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("spam", id="single"),
        pytest.param("spam eggs", id="one_arg"),
        pytest.param("spam eggs,parrot", id="two_args"),
        pytest.param("spam eggs, ex parrot", id="space_arg"),
        pytest.param("spam a\\,b,c", id="escaped_one"),
        pytest.param("spam a\\,b\\,c", id="escaped_two"),
        pytest.param("   spam   ", id="spaces"),
    ],
)
def test_roundtrip_action(text):
    act_type, args = parse_action_string(text)
    reconstructed = reconstruct_action(act_type, args)
    act_type2, args2 = parse_action_string(reconstructed)
    assert act_type == act_type2
    assert args == args2


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("spam eggs", id="basic"),
        pytest.param("spam eggs, parrot", id="one_arg"),
        pytest.param("spam eggs  ex parrot, cheese shop", id="multi"),
        pytest.param("spam eggs, a\\,b,c", id="escaped_one"),
        pytest.param("spam eggs, a\\,b\\,c", id="escaped_two"),
        pytest.param(" spam eggs parrot, cheese, ", id="spaces"),
    ],
)
def test_roundtrip_condition(text):
    operator, cond_type, args = parse_condition_string(text)
    reconstructed = reconstruct_condition(operator, cond_type, args)
    operator2, cond_type2, args2 = parse_condition_string(reconstructed)
    assert operator == operator2
    assert cond_type == cond_type2
    assert args == args2
