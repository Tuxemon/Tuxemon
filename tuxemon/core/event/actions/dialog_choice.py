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

import logging
from functools import partial

from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.locale import replace_text

logger = logging.getLogger(__name__)


class DialogChoiceAction(EventAction):
    """ Asks the player to make a choice.

    Valid Parameters: choice1:choice2, var_key
    """
    name = "dialog_choice"
    valid_parameters = [
        (str, "choices"),
        (str, "variable")
    ]

    def start(self):
        def set_variable(var_value):
            player.game_variables[self.parameters.variable] = var_value
            self.session.client.pop_state()

        player = self.session.player

        # perform text substitutions
        choices = replace_text(self.session, self.parameters.choices)

        # make menu options for each string between the colons
        var_list = choices.split(":")
        var_menu = list()
        for val in var_list:
            var_menu.append((val, val, partial(set_variable, val)))

        self.open_choice_dialog(self.session, var_menu)

    def update(self):
        if self.session.client.get_state_by_name("ChoiceState") is None:
            self.stop()

    def open_choice_dialog(self, session, menu):
        logger.info("Opening choice window")
        return session.client.push_state("ChoiceState", menu=menu)
