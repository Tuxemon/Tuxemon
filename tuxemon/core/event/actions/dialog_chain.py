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

from tuxemon.core.locale import replace_text
from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.tools import open_dialog
from tuxemon.core.graphics import get_avatar

logger = logging.getLogger(__name__)


class DialogChainAction(EventAction):
    """ Opens a dialog and waits.  Other dialog chains will add text to the dialog
        without closing it.  Dialog chains must be ended with the ${{end}} keyword.

    Valid Parameters: text_to_display

    You may also use special variables in dialog events. Here is a list of available variables:

    * ${{name}} - The current player's name.
    * ${{end}} - Ends the dialog chain.

    **Examples:**

    >>> action.__dict__
    {
        "type": "dialog_chain",
        "parameters": [
            "Red:\\n This is some dialog!"
        ]
    }

    """
    name = "dialog_chain"
    valid_parameters = [
        (str, "text"),
        (str, "avatar")
    ]

    def start(self):
        # hack to allow unescaped commas in the dialog string
        text = ', '.join(self.raw_parameters)
        text = replace_text(self.session, text)

        # If text is "${{end}}, then close the current dialog
        if not text == "${{end}}":
            self.stop()

            # is a dialog already open?
            dialog = self.session.client.get_state_by_name("DialogState")

            if dialog:
                # yes, so just add text to it
                dialog.text_queue.append(text)
            else:
                # no, so create new dialog with this line
                avatar = get_avatar(self.session, self.parameters.avatar)
                self.open_dialog(text, avatar)

    def update(self):
        # hack to allow unescaped commas in the dialog string
        text = ', '.join(self.raw_parameters)
        if text == "${{end}}":
            if self.session.client.get_state_by_name("DialogState") is None:
                self.stop()

    def open_dialog(self, initial_text, avatar):
        logger.info("Opening chain dialog window")
        open_dialog(self.session, [initial_text], avatar)
