"""
This module is for handling breaking changes to the save file.

Renaming maps:
  - Increment the value of SAVE_VERSION (e.g. from 1 to 2)
  - Add an entry to MAP_RENAMES consisting of:
    - The previous value of SAVE_VERSION (e.g. 1)
    - Pairs of:
        - The name of each map that has been renamed (the key)
        - The new name of the map (the value)
    Keys and values are separated by colons, each key-value pair is separated by a comma
    e.g.
        MAP_RENAMES = {
            # 0: {'before1.tmx': 'after1.tmx', 'before2.tmx': 'after2.tmx'}
        }

Other changes:
    - Increment the value of SAVE_VERSION
    - Amend the `upgrade_save` function as necessary
"""

SAVE_VERSION = 1
MAP_RENAMES = {
    # 0: {'before1.tmx': 'after1.tmx', 'before2.tmx': 'after2.tmx'}
}


def update_current_map(version, save_data):
    if version in MAP_RENAMES:
        new_name = MAP_RENAMES[version].get(save_data['current_map'])
        if new_name:
            save_data['current_map'] = new_name


def upgrade_save(save_data):
    version = save_data.get("version", 0)
    for i in range(version, SAVE_VERSION):
        update_current_map(i, save_data)
        if i == 0:
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
    return save_data
