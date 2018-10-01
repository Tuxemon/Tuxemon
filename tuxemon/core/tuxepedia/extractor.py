"""
    Tuxepedia HTML extractor

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""

from contextlib import contextmanager
import logging
import sqlite3

from lxml import html
import requests

from . import RESOURCE_PATHS


class TuxepediaWebExtractor:
    """requests + lxml wrapper class to extract Tuxemon
    information from the Tuxepedia website"""

    def __init__(self, web_path):
        """

        :param web_path: root path of the Tuxepedia website
        """

        self.web_path = web_path
        self.db_connection = None

        # TODO: add more Web params, like 'Content-Type' as needed
        self.headers = {'User-agent': 'Mozilla/5.0'}

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

    def url_to_html(self, url, params, headers = None):
        """Extract Web content into an HTML tree object

        :param url: URL path string
        :param params: requests auxiliary params
        :param headers: extra header fields needed for the request
        :return: HTML tree object or None on failure
        """

        content = self._exec_request(url, params, headers)

        if content is None:
            self.get_logger().warning("Couldn't retrieve"
                                      " content from {}".format(url))
            return None

        return html.fromstring(content)

    def _exec_request(self, url, params, headers = None):
        """Extract Web content

        :param url: URL path string
        :param params: requests auxiliary params
        :param headers: extra header fields needed for the request
        :return: request object/JSON or None on failure
        """

        if headers is None:
            headers = self.headers
        else:
            headers = {**self.headers, **headers}

        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            return None

        return response.content
