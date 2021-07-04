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

    def postcmd(self, stop: bool, line: str) -> bool:
        """
        If the application has exited, exit here as well.

        Parameters:
            line: Ignored.

        """
        # Check to see if we have exited
        return self.app.exit
