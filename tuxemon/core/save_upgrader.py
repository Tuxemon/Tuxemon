#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# core.save_upgrader Handle save file backwards compatability
#
#

"""
This module is for handling breaking changes to the save file.

Renaming maps:
  - Increment the value of SAVE_VERSION (e.g. from 1 to 2)
  - Add an entry to MAP_RENAMES consisting of:
    - The previous value of SAVE_VERSION (e.g. 1) mapping to
    - A 'dictionary' made up of pairs of:
        - The name of each map that has been renamed (the key)
        - The new name of the map (the value)
    Keys and values are separated by colons, each key-value pair is separated by a comma
    e.g.
        MAP_RENAMES = {
            # 1: {'before1.tmx': 'after1.tmx', 'before2.tmx': 'after2.tmx'},
        }

Other changes:
(If you have changed the codebase in such a way that older save files cannot be loaded)
    - Increment the value of SAVE_VERSION
    - Amend the `upgrade_save` function as necessary
"""

SAVE_VERSION = 1
MAP_RENAMES = {
    # 0: {'before1.tmx': 'after1.tmx', 'before2.tmx': 'after2.tmx'},
}


def upgrade_save(save_data):
    if 'steps' not in save_data['game_variables']:
        save_data['game_variables']['steps'] = 0

    version = save_data.get("version", 0)
    for i in range(version, SAVE_VERSION):
        _update_current_map(i, save_data)
        if i == 0:
            _remove_slug_prefixes(save_data)
    return save_data


def _update_current_map(version, save_data):
    if version in MAP_RENAMES:
        new_name = MAP_RENAMES[version].get(save_data['current_map'])
        if new_name:
            save_data['current_map'] = new_name


def _remove_slug_prefixes(save_data):
    """
    Slugs used to be prefixed by their type
    Before: item_potion, txmn_rockitten
    After: potion, rockitten
    """
    def fix_items(data):
        return {
            key.partition("_")[2]: num
            for key, num in data.items()
        }
    chest = save_data.get('storage', {})
    save_data['inventory'] = fix_items(save_data.get('inventory', {}))
    chest['items'] = fix_items(chest.get('items', {}))

    for mons in save_data.get('monsters', []), chest.get('monsters', []):
        for mon in mons:
            mon['slug'] = mon['slug'].partition("_")[2]
