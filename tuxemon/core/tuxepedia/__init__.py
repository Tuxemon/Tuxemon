"""
    Tuxepedia module init

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""

from pathlib import Path


class RESOURCE_PATHS:
    """Listing of all resource paths for the Tuxepedia"""

    # TODO: add project root path from global constants if possible
    top = Path("tuxemon", "resources")

    database = top.joinpath("db", "tuxepedia", "tuxepedia.sqlite")

    sprites = top.joinpath("sprites", "tuxepedia")
