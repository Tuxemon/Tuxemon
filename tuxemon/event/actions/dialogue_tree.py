# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.tools import open_choice_dialog, open_dialog
from tuxemon.ui.menu_options import ChoiceOption, MenuOptions

if TYPE_CHECKING:
    from tuxemon.db import DialogueChoice, DialogueNode
    from tuxemon.npc import NPC
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class DialogTreeAction(EventAction):
    """
    Presents a branching dialogue tree to the character, allowing them
    to make choices that affect game variables and determine the flow of
    conversation.

    Script usage:
        .. code-block::

            dialogue_tree <character> <dialogue_id>

    Script parameters:
        character: The NPC identifier whose dialogue tree will be used.
        dialogue_id: The identifier of the specific dialogue tree to
            present.
    """

    name = "dialogue_tree"
    character: str
    dialogue_id: str

    def start(self, session: Session) -> None:
        char = get_npc(session, self.character)
        if not char:
            logger.debug(f"NPC '{self.character}' not found.")
            return

        if char.dialogue is None:
            logger.debug(f"NPC '{self.character}' has no dialogue object.")
            return

        dialog_trees = char.dialogue.default.dialogtrees
        if not dialog_trees:
            logger.debug(
                f"NPC '{self.character}' has no dialogue trees defined."
            )
            return

        dialog_tree = dialog_trees.get(self.dialogue_id)
        if dialog_tree is None:
            logger.debug(
                f"Dialogue tree '{self.dialogue_id}' not found for NPC '{self.character}'."
            )
            return

        self._traverse_node(session, char, dialog_tree)

    def _traverse_node(
        self, session: Session, char: NPC, node: DialogueNode
    ) -> None:
        npc_text = T.translate(node.slug)

        visible_choices = [
            choice
            for choice in node.choices
            if is_choice_visible(char, choice)
        ]

        if not visible_choices:
            open_dialog(session.client, [npc_text])
            session.client.remove_state_by_name("DialogState")
            logger.debug(
                f"Removed DialogState after final dialogue: {node.slug}"
            )
            return

        def make_action(choice: DialogueChoice) -> ChoiceOption:
            choice_text = T.translate(choice.slug)
            next_node = choice.next_node

            def _next(_: object = None) -> None:
                logger.debug(f"Player selected choice: {choice.slug}")
                if choice.variable and choice.value is not None:
                    char.game_variables[choice.variable] = choice.value
                    logger.debug(
                        f"Set NPC variable '{choice.variable}' to '{choice.value}'"
                    )

                session.client.remove_state_by_name("ChoiceState")
                session.client.remove_state_by_name("DialogState")
                logger.debug(
                    f"Removed ChoiceState and DialogState after selection."
                )

                if next_node:
                    logger.debug(f"Proceeding to next node: {next_node.slug}")
                    self._traverse_node(session, char, next_node)
                else:
                    logger.debug("No next node. Dialogue ends here.")

            return ChoiceOption(
                key=choice.slug, display_text=choice_text, action=_next
            )

        options = [make_action(choice) for choice in visible_choices]

        open_dialog(session.client, [npc_text])
        logger.debug(f"Opened DialogState with NPC text: {node.slug}")

        open_choice_dialog(
            client=session.client,
            menu=MenuOptions(options),
            escape_key_exits=True,
        )
        logger.debug(
            f"Opened ChoiceState with options: {[choice.slug for choice in visible_choices]}"
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("ChoiceState")
        except ValueError:
            self.stop()


def is_choice_visible(char: NPC, choice: DialogueChoice) -> bool:
    # Positive conditions
    if choice.variables:
        for cond in choice.variables:
            for var, val in cond.items():
                if char.game_variables.get(var) != val:
                    return False

    # Negated conditions
    if choice.negated_variables:
        for cond in choice.negated_variables:
            for var, val in cond.items():
                if char.game_variables.get(var) == val:
                    return False

    return True
