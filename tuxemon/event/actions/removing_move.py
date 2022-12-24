from __future__ import annotations

import logging
import uuid
from functools import partial
from typing import NamedTuple, Optional, Union, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.npc import NPC
from tuxemon.states.dialog import ChoiceState
from tuxemon.tools import open_choice_dialog

logger = logging.getLogger(__name__)


class RemovingMoveActionParameters(NamedTuple):
    npc_slug: Union[str, None]


# noinspection PyAttributeOutsideInit
@final
class RemovingMoveAction(EventAction[RemovingMoveActionParameters]):
    """
    It removes a chosen technique from the monster moves.

    Script usage:
        .. code-block::

            removing_move [npc_slug]

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").

    """

    name = "removing_move"
    param_class = RemovingMoveActionParameters

    def start(self) -> None:
        def set_variable(var_value: str) -> None:
            if len(mon.moves) > 1:
                mon.moves.remove(var_value)
                self.session.client.pop_state()
            else:
                self.session.client.pop_state()

        npc_slug = self.parameters.npc_slug

        trainer: Optional[NPC]
        if npc_slug is None:
            trainer = self.session.player
        else:
            trainer = get_npc(self.session, npc_slug)

        assert trainer, "No Trainer found with slug '{}'".format(
            npc_slug or "player"
        )

        monster_id = uuid.UUID(trainer.game_variables["monster_remove_moves"])

        mon = trainer.find_monster_by_id(monster_id)
        if mon is None:
            logger.debug(
                "Monster not found in party, searching storage boxes."
            )
            mon = trainer.find_monster_in_storage(monster_id)

        if mon is None:
            logger.error(
                f"Could not find the monster with instance id {monster_id}"
            )
            return

        var_list = mon.moves
        var_menu = list()

        for val in var_list:
            text = T.translate(val.slug)
            var_menu.append((text, text, partial(set_variable, val)))

        open_choice_dialog(
            self.session,
            menu=var_menu,
            escape_key_exits=True,
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(ChoiceState)
        except ValueError:
            self.stop()
