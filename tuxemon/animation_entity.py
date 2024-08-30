# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Iterable

from pygame.surface import Surface

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.graphics import create_animation, load_frames_files

logger = logging.getLogger(__name__)


class AnimationEntity:
    """Holds all the values for animations."""

    def __init__(
        self,
        slug: str,
        duration: float = prepare.FRAME_TIME,
        loop: bool = False,
    ) -> None:
        self.slug: str = ""
        self.duration: float = duration
        self.loop: bool = loop
        self.file: str = ""
        self.directory: str = ""
        self.frames: Iterable[Surface] = []
        self.load(slug)

    def load(self, slug: str) -> None:
        """Loads animation."""
        try:
            results = db.lookup(slug, table="animation")
        except KeyError:
            raise RuntimeError(f"Animation {slug} not found")

        self.slug = results.slug
        self.file = results.file

        self.directory = prepare.fetch("animations", self.file)
        self.frames = load_frames_files(self.directory, self.slug)
        self.play = create_animation(self.frames, self.duration, self.loop)
