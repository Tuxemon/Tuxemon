"""
Not really a test.  Read all monsters and generate json output
suitable to use as a random encounter.

This file would be useful for maintaining a master random encounter
file, or for making new ones.

Currently, reads and uses all, eventually, may be useful to accept
command line arguments to customize

-Leif
"""
from __future__ import print_function

import json
from glob import glob
from os.path import join, normpath

# assume run from tests folder
monster_folder = normpath('../tuxemon/resources/db/monster/')
monster_glob = join(monster_folder, '*.json')

# skip monsters that are not ready for the game
blacklist = ['txmn_template']


def generate_monster_section(monster):
    d = dict()
    d['monster'] = monster['slug']
    d['encounter_rate'] = 1
    d['level_range'] = [1, 6]
    return d


def generate_list():
    for fn in glob(monster_glob):
        with open(fn) as fp:
            data = json.load(fp)
        if data['slug'] not in blacklist:
            yield generate_monster_section(data)


master_data = dict()
master_data['id'] = 1
master_data['monsters'] = list(generate_list())

print(json.dumps(master_data))
