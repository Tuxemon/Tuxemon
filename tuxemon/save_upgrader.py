# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from tuxemon import db
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.save_state import SaveData
logger = logging.getLogger(__name__)

"""
Handles breaking changes to the save file format.

This module ensures that older save files remain compatible with newer
versions of the game by applying necessary upgrades.

Upgrade strategy:

1. **SAVE_VERSION**
    Increment this value whenever the save file structure changes in
        a way that older versions cannot load.
    Each version bump should correspond to a function in `VERSION_UPGRADES`.

2. **Versioned Upgrades**
    Add a function like `upgrade_from_vX_to_vY(save_data)` for each version
        bump.
    Register it in the `VERSION_UPGRADES` dictionary.
    These functions apply changes specific to that version transition.

3. **Universal Fixes**
    Some changes (e.g. renaming monsters or techniques) should be applied
        regardless of version.
    These are handled in `apply_universal_fixes(npc_state)` and are always
        run.

Example:
    SAVE_VERSION = 3

    def upgrade_from_v2_to_v3(save_data: dict[str, Any]) -> None:
        # Apply changes introduced in version 3
        pass

    VERSION_UPGRADES = {
        0: upgrade_from_v0_to_v1,
        1: upgrade_from_v1_to_v2,
        2: upgrade_from_v2_to_v3,
    }

Notes:
- Always update `SAVE_VERSION` when introducing breaking changes.
- Keep universal fixes minimal and focused on data consistency.
"""

SAVE_VERSION = 2


MONSTER_RENAMES: dict[str, str] = {"axylightl": "axolightl"}  # old: new
TECHNIQUE_RENAMES: dict[str, str] = {"venom": "caustic_spray"}  # old: new


def upgrade_from_v0_to_v1(save_data: dict[str, Any]) -> None:
    # Placeholder for any changes introduced in version 1
    pass


def upgrade_from_v1_to_v2(save_data: dict[str, Any]) -> None:
    logger.info("Applying upgrade from version 1 to 2")
    npc_state = save_data.get("npc_state", {})
    _handle_change_tuxepedia(npc_state)
    _handle_change_plague(npc_state)
    _handle_change_money(npc_state)
    _handle_change_teleport_faint(npc_state)
    _handle_change_contacts(npc_state)


def apply_universal_fixes(npc_state: dict[str, Any]) -> None:
    _handle_change_monster_name(npc_state)
    _handle_change_tech_slug(npc_state)


VERSION_UPGRADES: dict[int, Callable[[dict[str, Any]], None]] = {
    0: upgrade_from_v0_to_v1,
    1: upgrade_from_v1_to_v2,
}


def upgrade_save(save_data: dict[str, Any]) -> SaveData:
    """
    Updates savegame if necessary.
    This function can modify the passed save data.
    """
    if "npc_state" not in save_data:
        save_data = update_save_data(save_data)

    version = save_data.get("version", 0)
    for i in range(version, SAVE_VERSION):
        upgrade_func = VERSION_UPGRADES.get(i)
        if upgrade_func:
            upgrade_func(save_data)

    save_data["version"] = SAVE_VERSION
    apply_universal_fixes(save_data["npc_state"])
    return save_data  # type: ignore[return-value]


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


def _handle_change_contacts(save_data: dict[str, Any]) -> None:
    """
    Updates contacts field in the save data.
    """
    if "contacts" not in save_data:
        return
    else:
        new: dict[str, Any] = {}
        for key in save_data["contacts"].keys():
            new[key] = {"relationship_type": "unknown"}
        save_data["relationships"] = new
        del save_data["contacts"]


def _handle_change_teleport_faint(save_data: dict[str, Any]) -> None:
    """
    Updates tuxepedia field in the save data.
    """
    if "teleport_faint" not in save_data:
        for entry, value in save_data["game_variables"].items():
            if entry == "teleport_faint":
                new_value = value.split(" ")
                new_tuple = (
                    new_value[0],
                    int(new_value[1]),
                    int(new_value[2]),
                )
                save_data["teleport_faint"] = new_tuple


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


def _handle_change_tech_slug(save_data: dict[str, Any]) -> None:
    """
    Updates tech slug in the save data based on the TECH_RENAMES dictionary.
    """

    def update_moves(moves: list[dict[str, Any]]) -> None:
        for move in moves:
            if move["slug"] in TECHNIQUE_RENAMES:
                move["slug"] = TECHNIQUE_RENAMES[move["slug"]]

    # Update monsters in the save data
    for monster in save_data["monsters"]:
        update_moves(monster["moves"])

    # Update monsters in the monster boxes
    for value in save_data["monster_boxes"].values():
        for element in value:
            update_moves(element["moves"])
