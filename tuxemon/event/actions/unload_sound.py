# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class UnloadSoundAction(EventAction):
    """
    Unload a specific sound from memory cache, or all sounds if no filename is given.

    Script usage:
        .. code-block::

            unload_sound <filename>
            unload_sound

    Script parameters:
        filename: Name of the sound file to unload.
            If omitted, all cached sounds will be removed from memory.
    """

    name = "unload_sound"
    filename: str | None = None

    def start(self, session: Session) -> None:
        client = session.client
        if not self.filename:
            client.sound_manager.unload_all_sounds()
        else:
            client.sound_manager.unload_sound(self.filename)
