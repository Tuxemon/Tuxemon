"""
    Tuxepedia module init

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os.path


class WEB_PATHS:
    """Listing of Web content resource paths for the Tuxepedia"""

    tuxepedia = "https://wiki.tuxemon.org"

    # TODO: add xpath filters for other parts of the Tuxepedia as needed
    monsters_xpath = '//*[@id="mw-content-text"]/table[1]/tr[1]/td[1]/table'
    monster_sound_xpath = '//*[@id="mw-content-text"]/div[1]/a'
    monster_main_sprites = '//*[@id="mw-content-text"]/table[4]'


class RESOURCE_PATHS:
    """Listing of all resource paths for the Tuxepedia"""

    # TODO: add project root path from global constants if possible
    # main static resources path
    resources = os.path.join("tuxemon", "resources")

    database = os.path.join(resources, "db", "tuxepedia", "tuxepedia.sqlite")

    # tuxemon sprites and sound file paths
    monster_sprites = os.path.join(resources, "gfx", "sprites", "battle")
    monster_sounds = os.path.join(resources, "sounds", "tuxemon")

    # tuxemon JSON/YAML file paths
    monster_stats = os.path.join(resources, "db", "monster")
