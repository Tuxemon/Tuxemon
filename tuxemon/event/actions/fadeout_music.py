# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform import mixer

logger = logging.getLogger(__name__)


@final
@dataclass
class FadeoutMusicAction(EventAction):
    """
    Fade out the music over a set amount of time in milliseconds.

    Script usage:
        .. code-block::

            fadeout_music <duration>

    Script parameters:
        duration: Number of milliseconds to fade out the music over.

    """

    name = "fadeout_music"
    duration: int

    def start(self) -> None:
        mixer.music.fadeout(self.duration)
        if self.session.client.current_music["song"]:
            self.session.client.current_music["status"] = "stopped"
        else:
            logger.warning("Music cannot be paused, none is playing.")
