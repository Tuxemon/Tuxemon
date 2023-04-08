# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping

from tuxemon import formula
from tuxemon.db import SeenStatus
from tuxemon.technique.technique import Technique

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


def upgrade_save(save_data: Dict[str, Any]) -> SaveData:
    """
    Updates savegame if necessary.

    This function can modify the passed save data.

    Parameters:
        save_data: The save data.

    Returns:
        Modified save data.

    """
    if "steps" not in save_data["game_variables"]:
        save_data["game_variables"]["steps"] = 0
    if "gender_choice" not in save_data["game_variables"]:
        save_data["game_variables"]["gender_choice"] = "gender_male"
    if "date_start_game" not in save_data["game_variables"]:
        save_data["game_variables"][
            "date_start_game"
        ] = formula.today_ordinal()

    save_data["money"] = save_data.get("money", {})
    save_data["tuxepedia"] = save_data.get("tuxepedia", {})
    save_data["contacts"] = save_data.get("contacts", {})
    save_data["items"] = save_data.get("items", [])
    save_data["battles"] = save_data.get("battles", [])

    # upgrade data moves
    for ele1 in save_data["monsters"]:
        if ele1["moves"]:
            backup_moves = []
            for mov in ele1["moves"]:
                if isinstance(mov, str):
                    backup_moves.append(mov)
            if backup_moves:
                for tech in backup_moves:
                    t = Technique()
                    t.load(tech)
                    ele1["moves"].remove(t.slug)
                    ele1["moves"].append(
                        {
                            "slug": t.slug,
                            "power": t.power,
                            "potency": t.potency,
                            "accuracy": t.accuracy,
                        }
                    )

    for key, value in save_data["monster_boxes"].items():
        for ele2 in value:
            if ele2["moves"]:
                backup_tech = []
                for mov in ele2["moves"]:
                    if isinstance(mov, str):
                        backup_tech.append(mov)
                if backup_tech:
                    for tech in backup_tech:
                        t = Technique()
                        t.load(tech)
                        ele2["moves"].remove(t.slug)
                        ele2["moves"].append(
                            {
                                "slug": t.slug,
                                "power": t.power,
                                "potency": t.potency,
                                "accuracy": t.accuracy,
                            }
                        )

    # upgrade data battle_history
    if "battle_history" in save_data:
        for key, value in save_data["battle_history"].items():
            output, date = value
            save_data["battles"].append(
                {"opponent": key, "outcome": output, "date": date}
            )

    # fix name capture device -> tuxeball
    capture_device = [
        element
        for element in save_data["items"]
        if element["slug"] == "capture_device"
    ]
    if capture_device:
        for capture in save_data["items"]:
            if capture["slug"] == "capture_device":
                save_data["items"].append(
                    {
                        "slug": "tuxeball",
                        "quantity": capture["quantity"],
                        "instance_id": capture["instance_id"],
                    }
                )
                save_data["items"].remove(capture)

    # template
    if "template" not in save_data:
        save_data["template"] = save_data.get("template", [])
        save_data["template"].append(
            {
                "slug": "adventurer",
                "sprite_name": "adventurer",
                "combat_front": "adventurer",
            }
        )

    # trasfer data from "inventory" to "items"
    if "inventory" in save_data:
        for key, value in save_data["inventory"].items():
            save_data["items"].append({"slug": key, "quantity": value})

    # set as captured the party monsters
    if not save_data["tuxepedia"]:
        for mons in save_data.get("monsters", []):
            save_data["tuxepedia"][mons["slug"]] = SeenStatus.caught
        for monsters in save_data.get("monster_boxes", {}).values():
            for monster in monsters:
                save_data["tuxepedia"][monster["slug"]] = SeenStatus.caught

    # set money old savegames and avoid getting the starter
    if not save_data["money"]:
        save_data["money"]["player"] = 10000
        save_data["game_variables"]["xero_starting_money"] = "yes"
        save_data["game_variables"]["spyder_starting_money"] = "yes"
    # set phone old savegames
    if "visitedcottoncafe" in save_data["game_variables"]:
        if save_data["game_variables"]["visitedcottoncafe"] == "yes":
            checking = [
                element
                for element in save_data["items"]
                if element["slug"] == "nu_phone"
            ]
            if not checking:
                save_data["items"].append({"slug": "nu_phone", "quantity": 1})
                save_data["items"].append(
                    {"slug": "app_banking", "quantity": 1}
                )
                save_data["items"].append({"slug": "app_map", "quantity": 1})
                save_data["items"].append(
                    {"slug": "app_tuxepedia", "quantity": 1}
                )
    if "timberdantewarn" in save_data["game_variables"]:
        if save_data["game_variables"]["timberdantewarn"] == "yes":
            checking = [
                element
                for element in save_data["items"]
                if element["slug"] == "nu_phone"
            ]
            if not checking:
                save_data["items"].append({"slug": "nu_phone", "quantity": 1})
                save_data["items"].append(
                    {"slug": "app_banking", "quantity": 1}
                )
                save_data["items"].append({"slug": "app_map", "quantity": 1})
                save_data["items"].append(
                    {"slug": "app_tuxepedia", "quantity": 1}
                )
                save_data["items"].append(
                    {"slug": "app_contacts", "quantity": 1}
                )

    version = save_data.get("version", 0)
    for i in range(version, SAVE_VERSION):
        _update_current_map(i, save_data)
        if i == 0:
            _remove_slug_prefixes(save_data)
        if i == 1:
            _transfer_storage_boxes(save_data)

    return save_data  # type: ignore[return-value]


def _update_current_map(version: int, save_data: Dict[str, Any]) -> None:
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


def _remove_slug_prefixes(save_data: Dict[str, Any]) -> None:
    """
    Fixes slug names in old saves.

    Slugs used to be prefixed by their type.
    Before: item_potion, txmn_rockitten.
    After: potion, rockitten.

    Parameters:
        save_data: The save data.

    """

    def fix_items(data: Dict[str, Any]) -> Dict[str, Any]:
        return {key.partition("_")[2]: num for key, num in data.items()}

    chest = save_data.get("storage", {})
    save_data["inventory"] = fix_items(save_data.get("inventory", {}))
    chest["items"] = fix_items(chest.get("items", {}))

    for mons in save_data.get("monsters", []), chest.get("monsters", []):
        for mon in mons:
            mon["slug"] = mon["slug"].partition("_")[2]


def _transfer_storage_boxes(save_data: Dict[str, Any]) -> None:
    """
    Fixes storage boxes in old saves.

    Item and monster storage used to be handled in a single
    dictionary, with "item" and "monster" keys. Now they're two
    dictionaries where the keys are "boxes", like in other popular
    games of the genre. This also allows "hidden" boxes for scripts
    to move items and monsters around.

    Parameters:
        save_data: The save data.

    """
    locker = save_data.get("storage", {}).get("items", {})
    kennel = save_data.get("storage", {}).get("monsters", {})

    save_data["monster_boxes"] = dict()
    save_data["item_boxes"] = dict()

    save_data["monster_boxes"]["Kennel"] = kennel
    save_data["item_boxes"]["Locker"] = locker
