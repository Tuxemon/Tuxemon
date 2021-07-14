#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
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
#
#
# cli Command line module used for debugging.
#
#
from __future__ import annotations
import cmd
import code
import logging
import pprint
from tuxemon.db import db
import os
from threading import Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.client import Client

logger = logging.getLogger(__name__)


class CommandLine(cmd.Cmd):
    """
    A class to enable an interactive debug command line.

    Provides a full python shell to review
    and modify variables while the game is actively running.

    Parameters:
        app: The game object itself.

    To include the command line in the game, simply add the following line
    under the initialization of the main game:

    >>> def __init__(self):
    ...     self.cli = cli.CommandLine(self)

    """

    def __init__(self, app: Client) -> None:
        # Initiate the parent class
        cmd.Cmd.__init__(self)

        # Set up the command line prompt itself
        self.prompt = "Tuxemon>> "
        self.intro = (
            'Tuxemon CLI\nType "help", "copyright", "credits"'
            ' or "license" for more information.'
        )

        # set up a  pretty printer so that shit is formatted nicely
        self.pp = pprint.PrettyPrinter(indent=4)

        # start the CLI in a separate thread

        self.app = app
        self.cmd_thread = Thread(target=self.cmdloop)
        self.cmd_thread.daemon = True
        self.cmd_thread.start()

        # For executing actions like add_item,
        # to avoid defining this variable mutiple times
        self.action = app.event_engine.execute_action

    def emptyline(self) -> bool:
        """If an empty line was entered at the command line, do nothing."""
        return False

    def do_exit(self, line: str) -> bool:
        """
        Exit the program on "exit".

        If "exit" was typed on the command line, set the app's exit variable
        to True.

        Parameters:
            line: Ignored.

        """
        self.app.exit = True
        return True

    def do_quit(self, line: str) -> bool:
        """
        Exit the program on "quit".

        If "quit" was typed on the command line, set the app's exit variable
        to True.

        Parameters:
            line: Ignored.

        """
        self.app.exit = True
        return True

    def do_EOF(self, line: str) -> bool:
        """
        Exit the program on EOF.

        If you press CTRL-D on the command line, set the app's exit variable
        to True.

        Parameters:
            line: Ignored.

        """
        return self.do_quit(line)

    def do_copyright(self, line: str) -> None:
        """
        Print the copyright information if "copyright" was entered.

        Parameters:
            line: Ignored.

        """
        print(
            "Tuxemon\nCopyright (C) 2014,"
            " William Edwards <shadowapex@gmail.com>,"
            " Benjamin Bean <superman2k5@gmail.com>"
        )

    def do_credits(self, line: str) -> None:
        """
        Print the copyright information if "credits" was entered.

        Parameters:
            line: Ignored.

        """
        self.do_copyright(line)

    def do_python(self, line: str) -> None:
        """
        Open a full python shell if "python" was typed in the command line.

        From here, you can look at and manipulate any variables in the
        application. This can be used to look at this
        instance's "self.app" variable which contains the game object.

        Parameters:
            line: Ignored.

        """
        print("Available variables:")
        print("self.pp.pprint(self.__dict__)")
        self.pp.pprint(self.__dict__)
        code.interact(local=locals())

    def do_add_monster(self, line:str) -> None:
        """
        Add monster to the player's party.
        Parameters:
            line: arguments
        """
        args = line.split(" ")
        try:
            monster = args[0]
            if len( monster.replace(" ", "") ) < 1:
                raise(ValueError)

            # Check, if level was added as an argument, if not, it will be set to 20
            try:
                level = args[1]
            except:
                level = 20
        except:
            print("Usage: add_monster <slug> [level]")
            return

        # Check, if the monster exists
        if not monster in db.database["monster"]:
            print(f"Monster {monster} doesn't exist!")
            return

        self.action("add_monster", (monster, level))
        print(f"Added {monster} to the party!")


    def do_add_item(self, line:str) -> None:
        """
        Add item to the player's bag.
        Parameters:
            line: arguments
        """
        args = line.split(" ")
        try:
            item = args[0]
            if len( item.replace(" ", "") ) < 1:
                raise(ValueError)

            # Check, if the amount of items was added as an argument
            try:
                amount = int(args[1])
            except IndexError:
                amount = 1
            except ValueError:
                # Move the handling one level down
                raise(ValueError)
        except:
            print("Usage: add_item <slug> [amount]")
            return

        # Check, if the monster exists
        if not item in db.database["item"]:
            print(f"Item {item} doesn't exist!")
            return

        for i in range(amount):
            self.action("add_item", (item,))
        self.action("update_inventory")
        print(f"Added {item} (amount: {amount}) to the bag!")

    def do_set_health(self, line:str) -> None:
        """
        Sets the monster's health.
        Parameters:
            line: arguments
        """
        # Usage info
        usage_info = "Usage: set_health <target_level> [slot]\ntarget_level must contain a number between 0 and 100\nIf no slot is provided, all monsters in the party will be selected"

        args = line.split(" ")

        # target_level is between 0 and 100, instead of original 0 to 1, to make it more user friendly
        try:
            target_health = int(args[0]) / 100
        except:
            print(usage_info)
            return

        try:
            slot = int(args[1])
            self.action("set_monster_health",(slot, target_health))
        except:
            self.action("set_monster_health", (None, target_health))

    def do_random_encounter(self, line:str) -> None:
        """
        Generates random encounter.
        Parameters:
            line: ignored
        """
        self.action("random_encounter", ("default_encounter",100))

    def do_trainer_battle(self, line:str) -> None:
        """
        Generates random encounter.
        Parameters:
            line: arguments
        """
        from tuxemon.event.actions.start_battle import StartBattleActionParameters
        usage_info = "Usage: trainer_battle <npc_slug>\nor\ntrainer_battle list\nnpc_slug - The npc in the npc database\nlist - List all npcs in the database"
        args = line.split(" ")
        try:
            trainer = args[0]

        except:
            print(usage_info)
            return

        if trainer == "list":
            for i in db.database["npc"]:
                if "monsters" in db.database["npc"][i]:
                    print(i)
        elif trainer in db.database["npc"]:
            self.action("create_npc", (trainer,7,6))
            self.action("start_battle", (StartBattleActionParameters(npc_slug=trainer)))
            self.action("remove_npc", (trainer,))

    def do_teleport(self, line:str) -> None:
        """
        Teleports the player to specified coordinates and (optionally) the specified map
        Parameters:
            line: arguments
        """
        usage_info = "Usage: teleport <x> <y> [map_file]"
        args = line.split(" ")

        try:
            x = args[0]
            y = args[1]

        except:
            print(usage_info)
            return

        try:
            map = args[2]
        except:
            map_filename = self.app.event_engine.current_map.data.filename
            map = os.path.split( map_filename )[1]

        self.action("teleport", (map, x, y))

    def do_whereami(self, line:str) -> None:
        """
        Prints the map the player is at to the console
        Parameters:
            line: ignored
        """
        map = os.path.split(self.app.event_engine.current_map.data.filename)[1]
        print(map)

    def postcmd(self, stop: bool, line: str) -> bool:
        """
        If the application has exited, exit here as well.

        Parameters:
            line: Ignored.

        """
        # Check to see if we have exited
        return self.app.exit
