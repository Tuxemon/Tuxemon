# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from tuxemon import db
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.save import SaveData

"""
This module is for handling breaking changes to the save file.

Renaming maps:
  - Increment the value of SAVE_VERSION (e.g. from 1 to 2)
  - Add an entry to MAP_RENAMES consisting of:
    - The previous value of SAVE_VERSION (e.g. 1) mapping to
    - A 'dictionary' made up of pairs of:
        - The name of each map that has been renamed (the key)
        - The new name of the map (the value)
    Keys and values are separated by colons, each key-value pair is separated
    by a comma, e.g.
        MAP_RENAMES = {
            # 1: {'before1.tmx': 'after1.tmx', 'before2.tmx': 'after2.tmx'},
        }

Other changes:
(If you have changed the codebase in such a way that older save files cannot
be loaded)
    - Increment the value of SAVE_VERSION
    - Amend the `upgrade_save` function as necessary
"""

SAVE_VERSION = 2
MAP_RENAMES: Mapping[int, Mapping[str, str]] = {
    # 0: {'before1.tmx': 'after1.tmx', 'before2.tmx': 'after2.tmx'},
}

MONSTER_RENAMES: dict[str, str] = {"axylightl": "axolightl"}  # old: new


def upgrade_save(save_data: dict[str, Any]) -> SaveData:
    """
    Updates savegame if necessary.

    This function can modify the passed save data.

    Parameters:
        save_data: The save data.

    Returns:
        Modified save data.
    """
    if "npc_state" not in save_data:
        save_data = update_save_data(save_data)

    save_data["npc_state"] = upgrade_npc_state(save_data["npc_state"])

    # version = save_data.get("version", 0)
    # for i in range(version, SAVE_VERSION):
    #    _update_current_map(i, save_data)

    return save_data  # type: ignore[return-value]


def upgrade_npc_state(npc_state: dict[str, Any]) -> dict[str, Any]:
    _handle_change_tuxepedia(npc_state)
    _handle_change_monster_name(npc_state)
    _handle_change_plague(npc_state)
    _handle_change_money(npc_state)

    return npc_state


def update_save_data(old_save_data: dict[str, Any]) -> dict[str, Any]:
    new_save_data: dict[str, Any] = {
        "screenshot": old_save_data["screenshot"],
        "screenshot_width": old_save_data["screenshot_width"],
        "screenshot_height": old_save_data["screenshot_height"],
        "time": old_save_data["time"],
        "version": old_save_data["version"],
        "npc_state": {},
    }

    # Move NPC state information inside the "npc_state" key
    for key, value in old_save_data.items():
        if key not in [
            "screenshot",
            "screenshot_width",
            "screenshot_height",
            "time",
            "version",
        ]:
            new_save_data["npc_state"][key] = value

    return new_save_data


def _handle_change_tuxepedia(save_data: dict[str, Any]) -> None:
    """
    Updates tuxepedia field in the save data.
    """
    for entry, value in save_data["tuxepedia"].items():
        if value in ("seen", "caught"):
            save_data["tuxepedia"][entry] = {
                "status": value,
                "appearance_count": 1,
            }


def _handle_change_money(save_data: dict[str, Any]) -> None:
    """
    Updates money field in the save data.
    """
    new_money: dict[str, Any] = {"money": 0, "bank_account": 0, "bills": {}}
    if "bills" in save_data["money"] and isinstance(
        save_data["money"]["bills"], dict
    ):
        return
    else:
        for entry, value in save_data["money"].items():
            if entry == "player":
                new_money["money"] = value
            elif entry == "bank_account":
                new_money["bank_account"] = value
            elif entry.startswith("bill_"):
                new_money["bills"][entry] = {
                    "amount": value,
                }
        save_data["money"] = new_money


def _handle_change_plague(save_data: dict[str, Any]) -> None:
    """
    Updates monster plague field in the save data.
    """

    def change_plague(monster: dict[str, Any]) -> None:
        if not isinstance(monster["plague"], dict):
            if monster["plague"] == "infected":
                monster["plague"] = {"spyderbite": db.PlagueType.infected}
            elif monster["plague"] == "inoculated":
                monster["plague"] = {"spyderbite": db.PlagueType.inoculated}
            else:
                monster["plague"] = {}

    # Update monsters in the save data
    for monster in save_data["monsters"]:
        change_plague(monster)

    # Update monsters in the monster boxes
    for value in save_data["monster_boxes"].values():
        for element in value:
            change_plague(element)


def _handle_change_monster_name(save_data: dict[str, Any]) -> None:
    """
    Updates monster names and slugs in the save data based on the MONSTER_RENAMES dictionary.
    """

    def update_monster(monster: dict[str, Any]) -> None:
        if monster["slug"] in MONSTER_RENAMES:
            new_name = MONSTER_RENAMES[monster["slug"]]
            monster["name"] = T.translate(new_name)
            monster["slug"] = new_name

    # Update monsters in the save data
    for monster in save_data["monsters"]:
        update_monster(monster)

    # Update monsters in the monster boxes
    for value in save_data["monster_boxes"].values():
        for element in value:
            update_monster(element)

    # Update monster names in the tuxepedia
    save_data["tuxepedia"] = {
        MONSTER_RENAMES.get(entry, entry): {
            "status": value.get("status", value),
            "appearance_count": value.get("appearance_count", 1),
        }
        for entry, value in save_data["tuxepedia"].items()
    }


def _update_current_map(version: int, save_data: dict[str, Any]) -> None:
    """
    Updates current map if necessary.

    Parameters:
        version: The version of the saved data.
        save_data: The save data.

    """
    if version in MAP_RENAMES:
        new_name = MAP_RENAMES[version].get(save_data["current_map"])
        if new_name:
            save_data["current_map"] = new_name
