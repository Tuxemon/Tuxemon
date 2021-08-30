import urllib.request

from tuxemon.constants import paths
import pathlib
import os
import json
import zipfile


class Manager:

    def __init__(self, *other_urls, caching=False):
        # TODO: Recreate the __init__


        if len(other_urls) == 0:
            other_urls = ["http://127.0.0.1"]
        packages_path = os.path.join(paths.CACHE_DIR, "packages")

        self.url = other_urls
        self.packages = []

        print(self.url, type(self.url))
        for i in self.url[0]:
            print(i, type(i))
            for package in self.update(i):
                #package["repo"] = i
                print(f"DEBUG: {package}")
                self.packages.append(package)
            #print(self.packages)
        print(self.packages)
            
        """
        for current_url in self.url:
            print(current_url)
            if caching:
                if pathlib.Path(packages_path + f"-{url.replace('/', '_')}").exists():
                    with open(packages_path + f"-{url.replace('/', '_')}") as file:
                        self.packages.append(json.loads(file.read()))
                else:
                    self.packages.append(self.update(current_url))
                    ##with urllib.request.urlopen(url + "/api/packages") as packages:
                    #    self.packages = json.loads(packages.read().decode("UTF-8"))

                    with open(packages_path + f"-{url.replace('/', '_')}", "w") as file:
                        file.write(json.dumps(self.packages, indent=4))
            else:
                self.packages.append(self.update(current_url))
"""

    def update(self, url):
        """Returns the response from the server"""
        with urllib.request.urlopen(url + "/api/packages") as packages:
            return json.loads(packages.read().decode("UTF-8"))

    def update_all(self):
        """
        Updates all packages in self.package.
        It automatically clears the self.package variable, and then
        populates it from the data from the repositories.
        """
        self.packages = []

        #print(self.url, type(self.url))
        for i in self.url[0]:
            print(i, type(i))
            for package in self.update(i):
                #package["repo"] = i
                print(f"DEBUG: {package}")
                self.packages.append(package)
            #print(self.packages)
        print(self.packages)
        """
        self.packages = []
        print(self.url)
        for url in self.url[0]:
            with urllib.request.urlopen(url + "/api/packages") as packages:
                self.packages.append(json.loads(packages.read().decode("UTF-8")))"""

    def list_packages(self):
        """Returns package dictionary, either from the server or the cache"""
        return self.packages

    def download_package(self, name, release, repo, dont_extract=False):
        """Downloads the specified package"""
        print(name, release, repo)
        url = str(repo) + f"/packages/{name}/releases/{str(release)}/download"
        filename = os.path.join(paths.CACHE_DIR + f"/{name}.{release}.zip")

        urllib.request.urlretrieve(url, filename=filename)

        outfolder = os.path.join(paths.BASEDIR, "mods", f"{name}")

        self.write_package_to_list(outfolder, name)

        if not dont_extract:
            self.extract(filename, outfolder)
            # Adding author name to prevent conflicts,
            # They will be resolved server side though ¯\_(ツ)_/¯ (now changed)
            with open(f"{outfolder}/meta.json", "w") as metafile:
                meta = self.get_package_info(name, repo)
                metafile.write(json.dumps(meta, indent=4))

    def download_packages(self, name, release, repo, dont_extract=False):
        """Same as the download_package(), but it includes dependency installing"""
        # Get info
        meta = self.get_package_info(author, name, repo)
        if "depends" in meta:
            dependencies = meta["dependencies"]

            for pack in dependencies:
               pass

    def extract(self, file, outfolder):
        """Extracts the specified zip archive to the mods directory"""
        with zipfile.ZipFile(file) as zip_:
            zip_.extractall(path=os.path.join(paths.BASEDIR, "mods", outfolder))

    def get_package_info(self, name, repo):
        """Get specified package info. Always downloads the info from the server."""
        with urllib.request.urlopen(repo + f"/api/packages/{name}") as packages:
            return json.loads(packages.read().decode("UTF-8"))

    def get_package_repo(self, name):
        """Reads the origin of an package.
        Returns None, if key 'mods' doesn't exist"""
        print()
        for i in self.packages:
            if i["name"] == name:
                print(i)
                return i["repo"]
                """
                if "repo" in i: return i["repo"]
                else: return None
                """
            else: print(f"{i} not in the name")

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
