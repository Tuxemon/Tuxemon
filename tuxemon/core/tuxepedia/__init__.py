"""
    Tuxepedia module init

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""

import os.path


class WEB_PATHS:
    """Listing of Web content resource paths for the Tuxepedia"""

    tuxepedia = "https://wiki.tuxemon.org"

    # TODO: add xpath filters for other parts of the Tuxepedia as needed
    monsters_xpath = '//*[@id="mw-content-text"]/table[1]/tr[1]/td[1]/table'


class RESOURCE_PATHS:
    """Listing of all resource paths for the Tuxepedia"""

    # TODO: add project root path from global constants if possible
    top = os.path.join("tuxemon", "resources")

    database = os.path.join(top, "db", "tuxepedia", "tuxepedia.sqlite")

    sprites = os.path.join(top, "sprites", "tuxepedia")
