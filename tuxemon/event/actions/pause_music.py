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
class PauseMusicAction(EventAction):
    """
    Pause the current music playback.

    Script usage:
        .. code-block::

            pause_music

    """

    name = "pause_music"

    def start(self) -> None:
        mixer.music.pause()
        if self.session.client.current_music["song"]:
            self.session.client.current_music["status"] = "paused"
        else:
            logger.warning("Music cannot be paused, none is playing.")
