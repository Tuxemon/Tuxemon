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
from functools import partial

from core.components.event.actions import replace_text
from core.components.event.eventaction import EventAction
from core.components.locale import translator
from core.tools import open_dialog

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)


class TranslatedDialogChoiceAction(EventAction):
    """Asks the player to make a choice.

    Valid Parameters: choice1:choice2,var_key
    """

    name = "translated_dialog_choice"

    def start(self):
        def set_variable(game, player, var_key, var_value):
            player.game_variables[var_key] = var_value
            self.game.pop_state()
            self.game.pop_state()

        # Get the player object from the self.game.
        player = self.game.player1

        # perform text substitutions
        text = str(self.parameters[0])
        text = replace_text(game, text)

        var_list = text.split(":")
        var_menu = list()

        for val in var_list:
            label = translator.translate(val).upper()
            var_menu.append((val, label, partial(set_variable, game, player, self.parameters[1], val)))

        # Open a dialog window in the current scene.
        if text == "${{end}}":
            self._done = self.game.get_state_name("DialogState") is None
        else:
            # is a dialog already open?
            dialog = self.game.get_state_name("DialogState")

            if dialog:
                dialog.text_queue.append(text)
            else:
                self.open_dialog(game, None, var_menu)

    def open_dialog(self, game, initial_text, menu=None):
        logger.info("Opening chain dialog window")
        open_dialog(game, None, menu)
