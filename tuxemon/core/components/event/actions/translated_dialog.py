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

from core.components.event.eventaction import EventAction


class TranslatedDialogAction(EventAction):
    """ Opens a dialog window with translated text according to the passed translation key. Parameters
    passed to the translation string will also be checked if a translation key exists.

    Valid Parameters: dialog_key,[var1=value1,var2=value2]

    You may also use special variables in dialog events. Here is a list of available variables:

    * ${{name}} - The current player's name.

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
        return self.game.event_engine.execute_action("translated_dialog_chain",
                                                     self.raw_parameters)
