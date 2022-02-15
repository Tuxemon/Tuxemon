"""

Combat related code that can be independent of the combat state.

Code here might be shared by states, actions, conditions, etc.

"""

from __future__ import annotations
import logging
from typing import Generator, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.player import Player
    from tuxemon.npc import NPC
    from tuxemon.monster import Monster


logger = logging.getLogger()


def check_battle_legal(player: Player) -> bool:
    """
    Checks to see if the player has any monsters fit for battle.

    Parameters:
        player: Player object.

    Returns:
        Whether the player has monsters that can fight.

    """
    # Don't start a battle if we don't even have monsters in our party yet.
    if len(player.monsters) < 1:
        logger.warning("Cannot start battle, player has no monsters!")
        return False
    else:
        if fainted_party(player.monsters):
            logger.warning("Cannot start battle, player's monsters are all DEAD.")
            return False
        else:
            return True


def check_status(monster: Monster, status_name: str) -> bool:
    return any(t for t in monster.status if t.slug == status_name)


def fainted(monster: Monster) -> bool:
    return check_status(monster, "status_faint") or monster.current_hp <= 0


def get_awake_monsters(player: NPC) -> Generator[Monster, None, None]:
    """
    Iterate all non-fainted monsters in party.

    Parameters:
        player: Player object.

    Yields:
        Non-fainted monsters.

    """
    for monster in player.monsters:
        if not fainted(monster):
            yield monster


def fainted_party(party: Sequence[Monster]) -> bool:
    return all(map(fainted, party))


def defeated(player: NPC) -> bool:
    return fainted_party(player.monsters)
