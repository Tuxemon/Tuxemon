#!/usr/bin/python
# Downloads all the monsters from the wiki and
# creates monsters and their sprites.
# Run set_movelist.py after this, as this script 
# deletes the movelist of every tuxemon.

from tuxemon.core.tuxepedia.api import TuxepediaStore

if __name__ == "__main__":

    # Fetch all our monster data.
    TuxepediaStore().sync_with_remote(completed_monsters=True)
