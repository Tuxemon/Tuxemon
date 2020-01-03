"""
    Tuxepedia backend handler

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import os
import os.path
import sqlite3
from contextlib import contextmanager

from . import RESOURCE_PATHS
from .extractor import TuxepediaWebExtractor, fix_name


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

    def sync_with_remote(self, completed_monsters):
        """Update local Tuxepedia content from Tuxepedia wiki pages"""

        # TODO: add version/timestamp check to decide whether a full pull is needed
        tuxepedia = TuxepediaWebExtractor()

        # scrape entire tuxemon database from Web
        # (sprites and sounds are downloaded as well)
        if completed_monsters:
            txmn_json_full = tuxepedia.get_completed_monsters()
        else:
            txmn_json_full = tuxepedia.get_monsters()

        for txmn_name in txmn_json_full:

            # full path to tuxemon JSON file
            txmn_json_path = os.path.join(RESOURCE_PATHS.monster_stats,
                                          fix_name(txmn_name.lower()) + ".json")

            # update tuxemon JSON record if it already exists
            if os.path.isfile(txmn_json_path):
                self.update_txmn_json(txmn_name, txmn_json_full[txmn_name])

                # log overwrite operation
                self.get_logger().debug("JSON record for {} exists and was overwritten.".format(txmn_name))

            # create new tuxemon JSON entry
            else:
                # make sure the tuxemon database directory exists
                os.makedirs(os.path.dirname(txmn_json_path), exist_ok=True)

                # dump tuxemon JSON
                with open(txmn_json_path, "w") as f:
                    json.dump(txmn_json_full[txmn_name], f, indent=4)

    def update_txmn_json(self, txmn_name, txmn_json_new, overwrite=True):
        """Update a tuxemon JSON file record

        :param txmn_name: tuxemon name
        :param txmn_json_new: new tuxemon JSON record
        :param overwrite: toggle to overwrite existing JSON fields
        """

        # full path to tuxemon JSON file
        txmn_json_path = os.path.join(RESOURCE_PATHS.monster_stats,
                                      fix_name(txmn_name.lower()) + ".json")

        # load previous tuxemon JSON from file
        with open(txmn_json_path) as f:
            txmn_json_old = json.load(f)

        # diff JSON records and add elements as needed
        for field in txmn_json_new:

            # replace existing fields
            if field in txmn_json_old and overwrite:
                txmn_json_old[field] = txmn_json_new[field]

            # add new fields
            elif field in txmn_json_new and field not in txmn_json_old:
                txmn_json_old[field] = txmn_json_new[field]

        # dump tuxemon JSON
        with open(txmn_json_path, "w") as f:
            json.dump(txmn_json_old, f, indent=4)

    def get_txmn_json(self, txmn_name):
        """Extract tuxemon JSON from file

        :param txmn_name: tuxemon name
        """

        txmn_json = None

        # full path to tuxemon JSON file
        txmn_json_path = os.path.join(RESOURCE_PATHS.monster_stats,
                                      txmn_name.lower() + ".json")

        if os.path.isfile(txmn_json_path):
            with open(txmn_json_path) as f:
                txmn_json = json.load(f)

        # report if no JSON record was found
        else:
            self.get_logger().warning("Valid JSON record for {} not found.".format(txmn_name))

        return txmn_json
