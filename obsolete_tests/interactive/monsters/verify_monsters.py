"""
Some basic checks to make sure the monster json is valid.
Assumes all JSON files are properly formatted.


Currently this will:
* verify that the techniques are defined in the techniques
* verify that the sprite files exist


Path checking is very forgiving and paths are normalized
as much as possible.  This permits paths to use windows
or unix style separators
* Should we change this?

Checking is done with slugs.

- Leif
"""
from __future__ import print_function

import json
from glob import glob
from os.path import join, basename, normpath, exists

# define the root folder used in the json files
sprite_root = 'gfx'

# assume run from test folder
resources_folder = normpath('../tuxemon/resources')

db_folder = join(resources_folder, 'db')
gfx_folder = join(resources_folder, 'gfx')

sprites_folder = join(gfx_folder, 'sprites', 'battle')
sprites_glob = join(sprites_folder, '*.*')

technique_folder = join(db_folder, 'technique')
technique_glob = join(technique_folder, '*.json')

monster_folder = join(db_folder, 'monster')
monster_glob = join(monster_folder, '*.json')


# use monster-formatted sprite section
# return a set of sprites, normalized
def normalize_sprites(data):
    return set(map(normpath, data.values()))


def get_slugs(pattern):
    retval = set()
    for fn in glob(pattern):
        with open(fn) as _fp:
            data = json.load(_fp)
        retval.add(data['slug'])
    return retval


def load_keys(filename):
    with open(filename) as _fp:
        return set(json.load(_fp).keys())


def print_list(sequence):
    for i in sorted(sequence):
        print("\t", i)


all_techniques = get_slugs(technique_glob)
errors = set()

for fn in glob(monster_glob):
    filename = basename(fn)
    print('verifying {}...'.format(filename))

    with open(fn) as fp:
        data = json.load(fp)

    # check that technique slugs exist
    for tech in data['moveset']:
        if tech['technique'] not in all_techniques:
            print('\tcannot find {}'.format(tech['technique']))
            errors.add(filename)

    # check that sprites exist
    sprites = normalize_sprites(data['sprites'])
    for fn in sprites:
        path = join(resources_folder, fn)
        if not exists(path):
            print('\tcannot find {}'.format(path))
            errors.add(filename)

if errors:
    print("These monsters are non-conforming:")
    print_list(errors)
else:
    print("It all checks out.")
