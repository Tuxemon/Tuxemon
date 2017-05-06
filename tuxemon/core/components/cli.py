#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# core.components.cli Command line module used for debugging.
#
#

import cmd
import code

class CommandLine(cmd.Cmd):
    """A class to enable an interactive debug command line. Provides a full python shell to review
    and modify variables while the game is actively running.

    :param app: The tuxemon.Game object of the game itself.

    :type app: tuxemon.Game

    To include the command line in the game, simply add the following line under the 
    initialization of the main game:

    >>> def __init__(self):
    ...     self.cli = core.cli.CommandLine(self) 

    """

    def __init__(self, app):

        # Initiate the parent class
        cmd.Cmd.__init__(self)

        # Set up the command line prompt itself
        self.prompt = "Tuxemon>> "
        self.intro = 'Tuxemon CLI\nType "help", "copyright", "credits" or "license" for more information.'

        # Import pretty print so that shit is formatted nicely
        import pprint
        self.pp = pprint.PrettyPrinter(indent=4)

        # Import threading to start the CLI in a separate thread
        from threading import Thread

        self.app = app
        self.cmd_thread = Thread(target=self.cmdloop)
        self.cmd_thread.daemon = True
        self.cmd_thread.start()


    def emptyline(self):
        """If an empty line was entered at the command line, do nothing.

        :param None:

        :rtype: None
        :returns: None

        """
        pass


    def do_exit(self, line):
        """If "exit" was typed on the command line, set the app's exit variable to True.

        :param None:  

        :rtype: None
        :returns: None

        """

        self.app.exit = True
        return True


    def do_quit(self, line):
        """If "quit" was typed on the command line, set the app's exit variable to True.                           

        :param None:  

        :rtype: None
        :returns: None

        """

        self.app.exit = True
        return True


    def do_EOF(self, line):
        """If you press CTRL-D on the command line, set the app's exit variable to True.                           

        :param None:  

        :rtype: None
        :returns: None

        """

        self.do_quit(line)
        return True


    def do_copyright(self, line):
        """Print the copyright information if "copyright" was entered.

        :param None:  

        :rtype: None
        :returns: None

        """

        print("Tuxemon\nCopyright (C) 2014, William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>")


    def do_credits(self, line):
        """Print the copyright information if "credits" was entered.

        :param None:  

        :rtype: None
        :returns: None

        """

        self.do_copyright(line)


    def do_python(self, line):
        """Open a full python shell if "python" was typed in the command line. From here, you can
        look at and manipulate any variables in the application. This can be used to look at this
        instance's "self.app" variable which contains the game object.

        :param None:  

        :rtype: None
        :returns: None

        """

        print("Available variables:")
        print("self.pp.pprint(self.__dict__)")
        self.pp.pprint(self.__dict__)
        code.interact(local=locals())


    def postcmd(self, stop, line):
        """If the application has exited, exit here as well.

        :param None:  

        :rtype: None
        :returns: None

        """

        # Check to see if we have exited
        if self.app.exit:
            return True


