"""
    Tuxepedia HTML extractor

    author: Andy Mender <andymenderunix@gmail.com>
    license: GPLv3
"""

import logging

from lxml import html
import requests


class TuxepediaWebExtractor:
    """requests + lxml wrapper class to extract Tuxemon
    information from the Tuxepedia website"""

    def __init__(self):

        self.db_connection = None

        # TODO: add more Web params, like 'Content-Type' as needed
        self.headers = {'User-agent': 'Mozilla/5.0'}

    def get_logger(self):
        """Access a custom class logger"""
        return logging.getLogger(self.__class__.__name__)

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
