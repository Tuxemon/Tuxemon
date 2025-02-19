# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import configparser
import json
import logging
import os
import pathlib
import shutil
import urllib.request
import zipfile
from typing import Any, Optional

import requests

from tuxemon.constants import paths
from tuxemon.mod_manager.symlink_missing import symlink_missing

logger = logging.getLogger(__name__)


def sanitize_paths(path: str) -> str:
    """Removes path specific characters like /."""
    for char in '/\\?%*:|"<>.,;= ':
        path = path.replace(char, "_")

    return path


class Manager:
    def __init__(
        self, *other_urls: Any, default_to_cache: bool = True
    ) -> None:
        """
        (basic) Mod managment library.
        """

        if len(other_urls) == 0:
            other_urls = ["http://127.0.0.1:5000"]

        self.packages_path = os.path.join(paths.CACHE_DIR, "packages")

        self.url = other_urls
        self.packages: list[Any] = []

        if default_to_cache:
            self.packages = self.read_from_cache()

    def write_to_cache(self) -> None:
        """Writes self.packages to the cache file"""

        with open(self.packages_path, "w") as file:
            file.write(json.dumps(self.packages, indent=4))

    def read_from_cache(self) -> Any:
        """Read self.packages from the cache file"""
        with open(self.packages_path) as file:
            return json.loads(file.read())

    def cache_to_pkglist(self) -> None:
        """
        Override self.packages with the cache.
        Uses self.packages = self.read_from_cache()
        """
        self.packages = self.read_from_cache()

    def update(self, url: str) -> Any:
        """Returns the response from the server"""
        packages = requests.get(url + "/api/packages")
        return packages.json()

    def update_all(self) -> None:
        """
        Updates all packages in self.package.
        It automatically clears the self.package variable, and then
        populates it from the data from the repositories.
        """
        self.packages = []

        for i in self.url:
            for package in self.update(i):
                self.packages.append(package)

        self.write_to_cache()

    def download_package(
        self,
        author: str,
        name: str,
        release: Optional[float],
        repo: Any = None,
        dont_extract: bool = False,
        install_deps: bool = True,
        installed: Any = None,
    ) -> None:
        """Downloads the specified package"""
        if repo is None:
            repo = self.get_package_repo(name)

            # Remove trailing slash
            if repo[-1] == "/":
                repo = repo[:-1]

        if release is None:
            logging.info("Getting latest release...")
            r = requests.get(repo + f"/api/packages/{author}/{name}/releases")
            logger.debug(r.text, author, name)
            logger.debug(repo + f"/api/packages/{author}/{name}/releases")
            # Get latest release (largest number).
            latest = 0
            for i in r.json():
                if i["id"] > latest:
                    latest = i["id"]
            release = latest

        # Sanitize author, name and release
        author = sanitize_paths(author)
        name = sanitize_paths(name)
        release = float(sanitize_paths(str(release)))
        logger.debug(
            " ".join(
                [
                    author,
                    name,
                    str(release),
                    repo,
                    str(dont_extract),
                    str(install_deps),
                    str(installed),
                ]
            )
        )
        url = (
            str(repo)
            + f"/packages/{author}/{name}/releases/{release}/download"
        )

        filename = os.path.join(
            paths.CACHE_DIR, f"downloaded_packages/{name}.{release}.zip"
        )

        logging.info(f"Downloading release {release} of {author}/{name}")

        # Based on answer from https://stackoverflow.com/a/16696317/14590202
        with requests.get(url, stream=True) as r:
            file_size = r.headers["content-length"]
            downloaded_size = 0
            r.raise_for_status()
            with open(filename, "wb") as file:
                for chunk in r.iter_content(chunk_size=8096):
                    file.write(chunk)
                    downloaded_size += 8096
                    logger.debug(f"Downloaded {downloaded_size} bytes")

        outfolder = os.path.join(paths.BASEDIR, "mods", name)

        self.write_package_to_list(os.path.relpath(outfolder), name)

        if not dont_extract:
            logging.info("Extracting...")
            self.install_local_package(filename, name=name)

        if install_deps:
            # This function calls download_package, might cause issues
            self.install_dependencies(
                author=author,
                name=name,
                repo=repo,
                dont_extract=dont_extract,
                done=installed,
            )
        logging.info("Done!")

    def install_dependencies(
        self,
        author: str,
        name: str,
        repo: Any,
        symlink: bool = True,
        **args: Any,
    ) -> None:
        """Recursively resolve dependencies and symlink them"""
        logger.debug(author, name, repo)
        # Request dependencies for specified package
        r = requests.get(
            f"{repo}/api/packages/{author}/{name}/dependencies/?only_hard=1"
        )
        if r.status_code != 200:
            raise ValueError(
                f"Requested {r.url}, received status code {r.status_code}"
            )
        logger.debug(r.text, author, name)
        dep_list = r.json()
        # Resolve dependencies
        for dependency in dep_list:
            for entry in dep_list[dependency]:
                for package in entry["packages"]:
                    package = sanitize_paths(package)
                    if os.path.exists(
                        os.path.join(paths.BASEDIR, "mods", package)
                    ):
                        continue
                    if package == "default":
                        continue
                    self.download_package(
                        package.split("/")[0],
                        package.split("/")[1],
                        release=None,
                        repo=repo,
                        install_deps=False,
                    )

    def parse_mod_conf(self, content: Any) -> Any:
        """
        Parses the minetest's mod.conf files.
        Returns: dict
        """
        out: dict[Any, Any] = {}
        for line in content.split("\n"):
            # Remove spaces and split into parts
            parts = line.split(" = ")
            if len(parts[0]) == 0:
                continue
            if parts[0] == "depends":
                element_list = parts[1].split(", ")
                parts[1] = element_list
                out = {**out, **{parts[0]: parts[1]}}
        return out

    def get_package_info(self, author: str, name: str, repo: Any) -> None:
        """Get specified package info. Always downloads the info from the server."""
        for char in '/\\?%*:|"<>.,;= ':
            name = name.replace(char, "_")
        r = requests.get(repo + "/api/packages/{author}/{name}/")

    def get_package_repo(self, name: str) -> Any:
        """Reads the origin of an package.
        Returns None, if key 'mods' doesn't exist"""
        for i in self.packages:
            if i["name"] == name:
                return i["repo"]
            else:
                continue

    def write_package_to_list(self, path_to_folder: str, name: str) -> None:
        """Writes specified package to the package list"""
        # Write the absolute path to the list
        with open(paths.USER_GAME_DATA_DIR + "/package.list", "w+") as file:
            if not len(file.read()) == 0:
                before = json.loads(file.read())
            else:
                before = {}

            to_append = {name: path_to_folder}
            after = {**before, **to_append}
            file.write(json.dumps(after, indent=4))

    def read_package_from_list(self, name: str) -> Any:
        """Reads path of the specified mod"""
        with open(paths.USER_GAME_DATA_DIR + "/package.list") as file:
            data = file.read()
            return json.loads(data)[name]

    def remove_package_from_list(self, name: str) -> None:
        """Removes specified package from the package list"""
        # Write the absolute path to the list
        with open(paths.USER_GAME_DATA_DIR + "/package.list", "r+") as file:
            data = file.read()
            if not len(data) == 0:
                before = json.loads(data)
            else:
                raise ValueError("The package.list is empty.")

            del before[name]
            file.write(json.dumps(before, indent=4))

    def remove_package(self, name: str) -> None:
        """Removes the local package"""
        # Get the path
        path = self.read_package_from_list(name)
        if os.path.isabs(path):
            raise OSError("Path is absolute")
        if path != sanitize_paths(path):
            raise ValueError("Detected incorrect characters in path")
        shutil.rmtree(path, ignore_errors=True)
        self.remove_package_from_list(name)

    def install_local_package(
        self,
        filename: str,
        name: str,
        download_deps: bool = False,
        link_deps: bool = False,
    ) -> None:
        """
        Installs local packages.
        Based on the download_package function, but without the downloads
        """
        outfolder = os.path.join(paths.BASEDIR, "mods")
        self.write_package_to_list(os.path.relpath(outfolder), name)
        with zipfile.ZipFile(filename) as zipf:
            free = shutil.disk_usage(os.getcwd()).free
            # get the filesize, based on https://stackoverflow.com/a/39953116/14590202
            zipsize = sum(zinfo.file_size for zinfo in zipf.filelist)
            if zipsize > free:
                raise OSError(
                    f"Zip contents are bigger than available disk space ({zipsize} > {free})"
                )
            zipf.extractall(path=os.path.join(outfolder, name))
