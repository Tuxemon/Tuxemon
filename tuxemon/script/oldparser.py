import re
from typing import List, Tuple

from natsort import natsorted

from tuxemon.event import MapCondition, MapAction


def split_escaped(text: str, deliminator: str = ",") -> List[str]:
    """
    Split a string by the specified deliminator excluding escaped deliminators.

    Parameters:
        text: The string to split.
        deliminator: The deliminator to split the string by.
    """
    # Split by "," unless it is escaped by a "\"
    split_list = re.split(r"(?<!\\)" + deliminator, text)

    # Remove the escape character from the split list
    split_list = [w.replace(r"\,", ",") for w in split_list]

    # strip whitespace around each
    split_list = [i.strip() for i in split_list]

    return split_list


def parse_action_string(text: str) -> Tuple[str, List]:
    words = text.split(" ", 1)
    act_type = words[0]
    if len(words) > 1:
        args = split_escaped(words[1])
    else:
        args = list()
    return act_type, args


def parse_condition_string(text: str) -> Tuple[str, str, List]:
    words = text.split(" ", 2)
    operator, cond_type = words[0:2]
    if len(words) > 2:
        args = split_escaped(words[2])
    else:
        args = list()
    return operator, cond_type, args


def parse_behav_string(behav_string: str) -> Tuple[str, List]:
    words = behav_string.split(" ", 1)
    behav_type = words[0]
    if len(words) > 1:
        args = split_escaped(words[1])
    else:
        args = list()
    return behav_type, args


def process_condition_string(
    text: str,
) -> Tuple[List[MapCondition], List[MapCondition]]:
    operator, cond_type, args = parse_condition_string(text)
    condition = MapCondition(cond_type, operator, args)
    return [condition], list()


def process_action_string(text: str) -> Tuple[List[MapCondition], List[MapCondition]]:
    act_type, args = parse_action_string(text)
    action = MapAction(act_type, args)
    return list(), [action]


def process_behav_string(text: str) -> Tuple[List[MapCondition], List[MapCondition]]:
    behav_type, args = parse_behav_string(text)
    if behav_type == "talk":
        condition = MapCondition("to_talk", "is", args)
        action = MapAction("npc_face", [args[0], "player"])
        return [condition], [action]
    else:
        raise ValueError(f"Bad event parameter: {text}")


def event_actions_and_conditions(items: List[Tuple[str, str]]):
    """Return list of acts and conditions from a list of labeled commands

    Parameters:
        items: label and command pairs, such as ["act0", "dialog ..."]
    """
    conds = []
    acts = []
    for key, value in natsorted(items):
        for arg, func in [
            ["cond", process_condition_string],
            ["act", process_action_string],
            ["behav", process_behav_string],
        ]:
            if key.startswith(arg):
                _conds, _acts = func(value)
                conds.extend(_conds)
                acts.extend(_acts)
        else:
            raise ValueError(f"Bad event parameter: {key}")
    return acts, conds
