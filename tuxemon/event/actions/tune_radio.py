# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.phone_radio import MAX_FREQ, MIN_FREQ

logger = logging.getLogger()


@final
@dataclass
class TuneRadioAction(EventAction):
    """
    Launches the NuPhoneRadio interface for a given character, optionally tuned
    to a specific frequency.

    This action transitions the game into a radio interface state, allowing the
    player to access broadcasts associated with a specific NPC. It can launch
    either the standard radio menu or the tuner interface, depending on whether
    a frequency is provided.

    This is typically used in scripted events to simulate tuning into a radio
    station from a character's perspective or location, enabling dynamic
    storytelling and immersive audio experiences.

    Script usage:
        .. code-block::

            tune_radio <character_slug>
            tune_radio <character_slug>[,frequency]

    Script parameters:
        character_slug: The slug of the character (NPC) whose context will be
            used to determine available radio stations and broadcasts.
        frequency: If provided, launches the tuner interface and attempts to
            tune directly to the specified frequency (in MHz). If omitted, the
            standard radio menu is shown instead.
    """

    name = "tune_radio"
    character_slug: str
    frequency: float | None = None

    def start(self, session: Session) -> None:
        self.session = session
        self.client = session.client

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name in {
            "NuPhoneRadioMenu",
            "NuPhoneRadioTuner",
        }:
            logger.error(
                f"The state '{self.client.current_state.name}' is already active. No action taken."
            )
            self.stop()
            return

        character = self.session.client.get_npc(self.character_slug)
        if character is None:
            logger.error(
                f"Character '{self.character_slug}' not found for radio tuning."
            )
            self.stop()
            return

        if self.frequency is not None:
            if not (MIN_FREQ <= self.frequency <= MAX_FREQ):
                logger.error(
                    f"Frequency {self.frequency} is out of FM range {MIN_FREQ}-{MAX_FREQ}."
                )
                self.stop()
                return

            self.client.push_state(
                "NuPhoneRadioTuner",
                character=character,
                frequency=self.frequency,
            )
        else:
            self.client.push_state("NuPhoneRadioMenu", character=character)

    def update(self, session: Session, dt: float) -> None:
        if not any(
            state.name in {"NuPhoneRadioMenu", "NuPhoneRadioTuner"}
            for state in session.client.active_states
        ):
            self.stop()
