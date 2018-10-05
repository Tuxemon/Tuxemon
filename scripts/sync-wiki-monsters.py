#!/usr/bin/python
# Downloads all the monsters from the wiki and
# creates monsters and their sprites.

from tuxemon.core.tuxepedia.api import TuxepediaStore

if __name__ == "__main__":

    # Fetch all our monster data.
    TuxepediaStore().sync_with_remote()
