#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
#

from tuxemon.core.event.eventcontext import EventContext
from tuxemon.core.tools import open_dialog


class DialogContext(EventContext):
    def __init__(self):
        # this is a potentially temporary solution to a problem with dialog chains
        self._dialog_chain_queue = list()
        self._menu = None

    def add_dialog(self, text):
        self._dialog_chain_queue.append(text)

    def add_avatar(self, avatar):
        self._avatar = avatar

    def add_menu(self, menu):
        self._menu = menu

    def execute(self, session):
        # Open a dialog window in the current scene.
        open_dialog(session, self._dialog_chain_queue, self._avatar, self._menu)
        self._dialog_chain_queue = list()
        self._avatar = None
        self._menu = None
