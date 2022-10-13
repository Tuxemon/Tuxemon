"""
Mod manager support module TuxemonContentServer
https://github.com/vXtreniusX/TuxemonContentServer
"""

import json
import os
import urllib.request

import requests

from tuxemon.constants import paths
from tuxemon.mod_manager import symlink_missing


def update(url):
    """Returns the response from the server"""
    packages = requests.get(url=url)
    print(packages.text)
    return packages.json()


def download_package(
    self,
    name,
    release,
    repo=None,
    dont_extract=False,
    install_deps=True,
    installed=None,
):
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
    filename = os.path.join(
        paths.CACHE_DIR,
        f"downloaded_packages/{name}.{release}.zip",
    )

    # Apparently this function is ported from urllib from python2.
    # Maybe replace this in the future?
    # https://docs.python.org/3/library/urllib.request.html#urllib.request.urlretrieve
    urllib.request.urlretrieve(url, filename=filename)

    outfolder = os.path.join(paths.BASEDIR, "mods", f"{name}")

    self.write_package_to_list(outfolder, name)

    if not dont_extract:
        self.extract(filename, outfolder)
        with open(f"{outfolder}/meta.json", "w") as metafile:
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
    name,
    release,
    repo,
    dont_extract=False,
    symlink=True,
    done=None,
):
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
        mainfolder = os.path.join(paths.BASEDIR, "mods", name)
        depfolder = os.path.join(paths.BASEDIR, "mods", pack)
        symlink_missing(mainfolder, depfolder)
    else:
        pass
