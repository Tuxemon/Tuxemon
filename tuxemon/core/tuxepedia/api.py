"""
    Tuxepedia backend handler

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""

from contextlib import contextmanager
import logging
import sqlite3

from . import RESOURCE_PATHS


class TuxepediaStore:
    """SQLite-based interface for the Tuxepedia backend"""

    def get_logger(self):
        """Access a custom class logger"""
        return logging.getLogger(self.__class__.__name__)

    @contextmanager
    def db_connect(self):
        """Connect to the SQLite database backend to store information"""

        self.connection = sqlite3.connect(RESOURCE_PATHS.database)

        yield self

        self.connection.close()
        self.connection = None

    @contextmanager
    def cursor(self):
        """Yield a cursor for database backend queries"""

        if self.connection is None:
            error_msg = "Cursor for db {} could not be created"
            error_msg = error_msg.format(RESOURCE_PATHS.database)

            self.get_logger().error(error_msg)

        yield self.connection.cursor()

        self.connection.commit()
