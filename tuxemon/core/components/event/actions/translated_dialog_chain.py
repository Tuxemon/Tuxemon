# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import

import logging

from tuxemon.core.components.event.actions import process_translate_text, replace_text
from tuxemon.core.components.event.eventaction import EventAction
from tuxemon.core.tools import open_dialog

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class TranslatedDialogChainAction(EventAction):
    """Opens a chain of dialogs in order. Dialog chain must be ended with the ${{end}} keyword.

    Valid Parameters: text_to_display

    You may also use special variables in dialog events. Here is a list of available variables:

    * ${{name}} - The current player's name.
    * ${{end}} - Ends the dialog chain.

    **Examples:**

    >>> action.__dict__
    {
        "type": "translated_dialog_chain",
        "parameters": [
            "received_x",
            "name=Potion"
        ]
    }

    """
    name = "translated_dialog_chain"
    valid_parameters = [(str, "key")]

    def start(self):
        key = self.parameters.key

        # If text is "${{end}}, then close the current dialog
        if key == "${{end}}":
            return

        self.stop()

        pages = process_translate_text(
            self.game,
            key,
            self.raw_parameters[1:],
        )

        dialog = self.game.get_state_name("DialogState")
        if dialog:
            dialog.text_queue += pages
        else:
            self.open_dialog(pages)

    def update(self):
        if self.parameters.key == "${{end}}":
            if self.game.get_state_name("DialogState") is None:
                self.stop()

    def open_dialog(self, pages):
        logger.info("Opening chain dialog window")
        open_dialog(self.game, pages)
