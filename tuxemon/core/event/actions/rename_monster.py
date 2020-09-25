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
# Contributor(s):
#
# Adam Chevalier <chevalierAdam2@gmail.com>
# 


from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.locale import T


class RenameMonsterAction(EventAction):
    """Opens the monster menu and text input screens to rename a selected monster.

    Valid Parameters: None
    """
    name = "rename_monster"
    valid_parameters = []

    def start(self):
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name("WorldState")
        if not world:
            return
    
        # pull up the monster menu so we know which one we are renaming
        menu = self.session.client.push_state("MonsterMenuState")
        menu.on_menu_selection = self.prompt_for_name

    def update(self):
        if self.session.client.get_state_by_name("MonsterMenuState") is None and self.session.client.get_state_by_name("InputMenu") is None:
            self.stop()

    def set_monster_name(self, name):
        self.monster.name = name
        self.session.client.get_state_by_name("MonsterMenuState").refresh_menu_items()

    def prompt_for_name(self, menu_item):
        self.monster = menu_item.game_object

        self.session.client.push_state(
            state_name="InputMenu",
            prompt=T.translate("input_monster_name"),
            callback=self.set_monster_name,
            escape_key_exits=False,
            initial=T.translate(self.monster.slug)
        )
