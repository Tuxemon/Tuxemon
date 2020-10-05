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

from tuxemon.core.locale import process_translate_text
from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.tools import open_dialog
from tuxemon.core.graphics import get_avatar

logger = logging.getLogger(__name__)


class TranslatedDialogAction(EventAction):
    """ Opens a dialog window with translated text according to the passed translation key. Parameters
    passed to the translation string will also be checked if a translation key exists.

    Valid Parameters: dialog_key,[var1=value1,var2=value2]

    You may also use special variables in dialog events. Here is a list of available variables:

    * ${{name}} - The current player's name.

    Parameters following the translation name may represent one of two things:
    If a parameter is var1=value1, it represents a value replacement.
    If it's a single value (an integer or a string), it will be used as an avatar image.
    TODO: This is a hack and should be fixed later on, ideally without overloading the parameters.

    **Examples:**

    >>> action.__dict__
    {
        "type": "translated_dialog",
        "parameters": [
            "received_x",
            "name=Potion"
        ]
    }

    """
    name = "translated_dialog"

    def start(self):
        key = self.raw_parameters[0]
        replace = []
        avatar = None
        for param in self.raw_parameters[1:]:
            if "=" in param:
                replace.append(param)
            else:
                avatar = get_avatar(self.session, param)

        self.open_dialog(
            process_translate_text(
                self.session,
                key,
                replace,
            ), avatar
        )

    def update(self):
        if self.session.client.get_state_by_name("DialogState") is None:
            self.stop()

    def open_dialog(self, pages, avatar):
        logger.info("Opening dialog window")
        open_dialog(self.session, pages, avatar)
