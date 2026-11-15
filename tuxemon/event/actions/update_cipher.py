# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class UpdateCipherAction(EventAction):
    """
    Updates the list of unlocked letters for a character used by the CipherProcessor.

    Script usage:

        .. code-block:: text

        update_cipher <character>[,letter]

    Parameters:

        character:
            Either "player" or npc slug name (e.g. "npc_maple").

        letter:
            A single uppercase letter (or multiple separated by ':') to add to
            the character's unlocked set. If omitted, no new letters will be added,
            but the CipherProcessor will be updated with the current unlocked state.
    """

    name = "update_cipher"
    character: str
    letters: str

    def start(self, session: Session) -> None:
        character = session.client.get_npc(self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            self.stop()
            return

        if self.letters:
            for letter in self.letters.split(":"):
                letter = letter.strip().upper()
                if not (len(letter) == 1 and letter.isalpha()):
                    raise ValueError(
                        f"Invalid letter '{letter}'. Must be a single uppercase A-Z character."
                    )
                character.unlocked_letters.add(letter)

        cipher_processor = session.client.cipher_processor
        if cipher_processor is None:
            logger.error("Cipher processor isn't enabled")
            self.stop()
            return
        cipher_processor.set_unlocked_letters(character.unlocked_letters)
