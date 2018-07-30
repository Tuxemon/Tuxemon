from __future__ import print_function

import glob
import json
from os.path import dirname, join, normpath
import unittest


RESOURCES_DIR = normpath(join(dirname(__file__), '../tuxemon/resources'))

# assume run from tests folder
MAP_ROOT = join(RESOURCES_DIR, 'maps')
NPC_ROOT = join(RESOURCES_DIR, 'db/npc')
SPRITE_ROOT = join(RESOURCES_DIR, 'sprites')

# If a sprite is deliberately partially implemented
SKIPPED_SPRITES = {
    # 'maple_back',
    # 'maple_back_walk',
}

SPRITES = {
    name.replace(SPRITE_ROOT + "/", "").split(".")[0].split('0')[0]
    for name in
    glob.glob(join(SPRITE_ROOT, '*.png'))
}
assert SPRITES, "No sprites found. Is the path correct?"


def load_keys(filename):
    with open(filename) as _fp:
        return set(json.load(_fp).keys())


def get_expected_sprites(slug):
    return {
        slug + "_back",
        slug + "_back_walk",
        slug + "_front",
        slug + "_front_walk",
        slug + "_left",
        slug + "_left_walk",
        slug + "_right",
        slug + "_right_walk",
    }


def get_missing_sprites():
    undefined = []
    partial = []
    for record_file in glob.glob(join(NPC_ROOT, '*.json')):
        with open(record_file) as r:
            sprite = json.load(r).get('sprite_name')
            if sprite is None:
                record_file = record_file.replace(NPC_ROOT + "/", "").replace(".json", "")
                undefined.append(record_file)
            else:
                expected = get_expected_sprites(sprite)
                partials = expected.difference(SPRITES).difference(SKIPPED_SPRITES)
                if partials:
                    partial += partials

    if undefined:
        print("No sprite defined for:")
        print("\t" + "\n\t".join(sorted(undefined)))
    if partial:
        print("Missing sprite for:")
        print("\t" + "\n\t".join(sorted(partial)))

    return not undefined and not partial


class TestSprites(unittest.TestCase):
    def test_missing(self):
        self.assertTrue(get_missing_sprites(), "Sprites are missing or undefined")


if __name__ == "__main__":
    get_missing_sprites()
