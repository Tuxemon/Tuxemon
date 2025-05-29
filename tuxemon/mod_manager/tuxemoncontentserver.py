# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Mod manager support module TuxemonContentServer
https://github.com/vXtreniusX/TuxemonContentServer
"""

import json
import urllib.request
from typing import Any

import requests

from tuxemon.constants import paths
from tuxemon.mod_manager.symlink_missing import symlink_missing


def update(url: str) -> Any:
    """Returns the response from the server"""
    packages = requests.get(url=url)
    print(packages.text)
    return packages.json()


def download_package(
    self,
    name: str,
    release: Any,
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

    # Sanitize name and release
    for char in '/\\?%*:|"<>.,;= ':
        name = name.replace(char, "_")
        release = str(release).replace(char, "_")

    url = str(repo) + f"/packages/{name}/releases/{str(release)}/download"
    filename = (
        paths.CACHE_DIR / "downloaded_packages" / f"{name}.{release}.zip"
    )

    # Apparently this function is ported from urllib from python2.
    # Maybe replace this in the future?
    # https://docs.python.org/3/library/urllib.request.html#urllib.request.urlretrieve
    urllib.request.urlretrieve(url, filename=filename)

    outfolder = paths.BASEDIR / "mods" / name

    self.write_package_to_list(outfolder, name)

    if not dont_extract:
        self.extract(filename, outfolder)
        with (outfolder / "meta.json").open("w") as metafile:
            meta = self.get_package_info(name, repo)
            metafile.write(json.dumps(meta, indent=4, sort_keys=False))

    if install_deps:
        # This function calls download_package, might cause issues
        self.install_dependencies(
            author=name,
            name=release,
            repo=repo,
            dont_extract=dont_extract,
            done=installed,
        )


def install_dependencies(
    self,
    name: str,
    release: Any,
    repo: Any,
    dont_extract: bool = False,
    symlink: bool = True,
    done: Any = None,
) -> None:
    """
    Same as the download_package(), but it includes dependency installing.
    When symlink is True, dependency's files will be linked.
    """
    for char in '/\\?%*:|"<>.,;= ':
        name = name.replace(char, "_")
    # Get info
    meta = self.get_package_info(name, repo)

    installed = done
    if installed is None:
        installed = [name]
    if "dependencies" in meta:
        dependencies = meta["dependencies"]

    for pack in dependencies:
        # Sanitize name and release
        for char in '/\\?%*:|"<>.,;= ':
            pack = str(pack).replace(char, "_")

        if pack in installed:
            continue

        self.download_package(
            pack,
            release,
            repo,
            dont_extract=dont_extract,
            installed=installed,
        )

        # Symlink deps
        mainfolder = paths.BASEDIR / "mods" / name
        depfolder = paths.BASEDIR / "mods" / pack
        symlink_missing(mainfolder.as_posix(), depfolder)
    else:
        pass
