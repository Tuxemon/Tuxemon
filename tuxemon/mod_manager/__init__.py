import urllib.request
import requests

from tuxemon.constants import paths
from tuxemon.symlink_missing import symlink_missing
import pathlib
import os
import json
import zipfile
import shutil
import configparser

def sanitize_paths(path):
    """Removes path specific characters like /."""
    for char in '/\\?%*:|"<>.,;= ':
        path = path.replace(char, "_")

    return path

class Manager:

    def __init__(self, *other_urls, default_to_cache=True):
        """
        (basic) Mod managment library.
        """

        if len(other_urls) == 0:
            other_urls = ["http://127.0.0.1:5000"]

        self.packages_path = os.path.join(paths.CACHE_DIR, "packages")

        self.url = other_urls
        self.packages = []

        if default_to_cache:
            self.packages = self.read_from_cache()

    def write_to_cache(self):
        """Writes self.packages to the cache file"""

        with open(self.packages_path, "w") as file:
            file.write(
                json.dumps(self.packages, indent=4)
            )
    def read_from_cache(self):
        """Read self.packages from the cache file"""
        with open(self.packages_path) as file:
            return json.loads(file.read())

    def cache_to_pkglist(self):
        """
        Override self.packages with the cache.
        Uses self.packages = self.read_from_cache()
        """
        self.packages = self.read_from_cache()

    def update(self, url):
        """Returns the response from the server"""
        packages = requests.get(url + "/api/packages")
        return packages.json()

    def update_all(self):
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

    def list_packages(self):
        """Returns package dictionary, either from the server or the cache"""
        return self.packages

    def download_package(self, author, name, release=None, repo=None, dont_extract=False, install_deps=True, installed=None):
        """Downloads the specified package"""
        if repo is None:
            repo = self.get_package_repo(name)

            # Remove trailing slash
            if repo[-1] == "/":
                repo = repo[:-1]

        if release is None:
            r = requests.get(repo + f"/api/packages/{author}/{name}/releases")
            print(r.text, author, name)
            print(repo + f"/api/packages/{author}/{name}/releases")
            # Get latest release (largest number).
            latest = 0
            for i in r.json():
                if i["id"] > latest:
                    latest = i["id"]
            release = latest

        # Sanitize name and release
        name = sanitize_paths(name)
        release = sanitize_paths(str(release))
        uwu = input( " ".join([author, name, release, repo, str(dont_extract), str(install_deps), str(installed)]) ) 
        url = str(repo) + f"/packages/{author}/{name}/releases/{str(release)}/download"

        filename = os.path.join(paths.CACHE_DIR, f"downloaded_packages/{name}.{release}.zip")

        # Apperantly this function is ported from urllib from python2.
        # Maybe replace this in the future?
        # https://docs.python.org/3/library/urllib.request.html#urllib.request.urlretrieve
        #urllib.request.urlretrieve(url, filename=filename)

        # Based on answer from https://stackoverflow.com/a/16696317/14590202
        with requests.get(url, stream=True) as r:
            file_size = r.headers["content-length"]
            downloaded_size = 0
            r.raise_for_status()
            with open(filename, "wb") as file:
                for chunk in r.iter_content(chunk_size=8096):
                    file.write(chunk)
                    downloaded_size += 8096
                    print(f"{downloaded_size}/{file_size}", int(file_size) - downloaded_size)

        outfolder = os.path.join(paths.BASEDIR, "mods")

        self.write_package_to_list(os.path.relpath(outfolder), name)

        if not dont_extract:
            with zipfile.ZipFile(filename) as zip_:
                print(zip_.namelist())
                zip_.extractall(path=os.path.join(paths.BASEDIR, "mods", outfolder))
            #self.extract(filename, outfolder)
            #with open(f"{outfolder}/meta.json", "w") as metafile:
            #    meta = self.get_package_info(name, repo)
            #    metafile.write(json.dumps(meta, indent=4, sort_keys=False))

        if install_deps:
            # This function calls download_package, might cause issues
            self.install_dependencies(name, release, repo, dont_extract=dont_extract, done=installed)

    def install_dependencies(self, author, name, repo, symlink=True, **args):
        """Recursively resolve dependencies and symlink them"""
        print(author, name, repo)
        # Request dependencies for specified package
        r = requests.get(f"https://content.minetest.net/api/packages/{author}/{name}/dependencies/?only_hard=1")
        #print(r.text, author, name)
        dep_list = r.json()
        # Resolve dependencies
        for dependency in dep_list:
            for entry in dep_list[dependency]:
                for package in entry["packages"]:
                    if os.path.exists(os.path.join(paths.BASEDIR, "mods", package)):
                        continue
                    self.download_package(
                        package.split("/")[0],
                        package.split("/")[1],
                        repo=repo,
                        install_deps=False
                        
                    )
                    

    """def install_dependencies(self, name, release, repo, dont_extract=False, symlink=True, done=None):
        "#""
        Same as the download_package(), but it includes dependency installing.
        When symlink is True, dependency's files will be linked.
        "#""
        name = sanitize_paths(name)
        # Get info
        with open(os.path.join(paths.BASEDIR, "mods", name, "mod.conf")) as file:
            raw_meta = file.read()
            meta = self.parse_mod_conf(raw_meta)
            
        installed = done
        if installed is None:
            installed = [name]
        if "depends" in meta:
            dependencies = meta["depends"]

            for pack in dependencies:
                # Sanitize name and release
                for char in '/\\?%*:|"<>.,;= ':
                    pack = str(pack).replace(char, "_")

                if pack in installed: continue
                
                
                self.download_package(pack, release, repo=repo, dont_extract=dont_extract, installed=installed)

                # Symlink deps
                mainfolder = os.path.join(paths.BASEDIR, "mods", name)
                depfolder = os.path.join(paths.BASEDIR, "mods", pack)
                symlink_missing(mainfolder, depfolder)
        else: pass
    """

    """    def parse_mod_conf(self, content):
        "#""
        Parses the minetest's mod.conf files.
        Returns: dict
        "#""
        out = {}
        for line in content.split("\n"):
            # Remove spaces and split into parts
            parts = line\
                .split(" = ")
            if len(parts[0]) == 0:
                continue
            if parts[0] == "depends":
                element_list = parts[1].split(", ")
                parts[1] = element_list
            out = {**out, **{parts[0]:parts[1]}}
        return out"""

    def get_package_info(self, author, name, repo):
        """Get specified package info. Always downloads the info from the server."""
        for char in '/\\?%*:|"<>.,;= ':
            name = name.replace(char, "_")
        r = requests.get(repo + "/api/packages/{author}/{name}/")

    def get_package_repo(self, name):
        """Reads the origin of an package.
        Returns None, if key 'mods' doesn't exist"""
        for i in self.packages:
            if i["name"] == name:
                return i["repo"]
            else: continue

    def write_package_to_list(self, path_to_folder, name):
        """Writes specified package to the package list"""
        # Write the absolute path to the list
        with open(paths.USER_GAME_DATA_DIR + "/package.list", "w+") as file:
            if not len(file.read()) == 0:
                before = json.loads(file.read())
            else:
                before = {}

            to_append = {name: path_to_folder}
            after = {**before, **to_append}
            file.write(
                json.dumps(after, indent=4)
            )

    def read_package_from_list(self, name):
        """Reads path of the specified mod"""
        with open(paths.USER_GAME_DATA_DIR + "/package.list") as file:
            data = file.read()
            return json.loads(data)[name]

    def remove_package_from_list(self, name):
        """Removes specified package from the package list"""
        # Write the absolute path to the list
        with open(paths.USER_GAME_DATA_DIR + "/package.list", "r+") as file:
            data = file.read()
            if not len(data) == 0:
                before = json.loads(data)
            else:
                raise ValueError("The package.list is empty.")

            del before[name]
            file.write(
                json.dumps(before, indent=4)
            )


    def remove_package(self, name):
        """Removes the local package"""
        # Get the path
        path = self.read_package_from_list(name)
        if os.path.isabs(path):
            raise IOError("Path is absolute")
        if path != sanitize_paths(path):
            raise ValueError("Detected incorrect characters in path")
        shutil.rmtree(path, ignore_errors=True)
        self.remove_package_from_list(name)
