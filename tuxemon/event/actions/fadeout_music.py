# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class FadeoutMusicAction(EventAction):
    """
    Fade out the music over a set amount of time in milliseconds.

    Script usage:
        .. code-block::

            fadeout_music [duration]

    Script parameters:
        duration: Number of milliseconds to fade out the music over.

    """

    name = "fadeout_music"
    duration: Optional[int] = None

    def start(self, session: Session) -> None:
        duration = (
            prepare.MUSIC_FADEOUT if self.duration is None else self.duration
        )
        session.client.current_music.stop(duration)
