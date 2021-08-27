import urllib.request

from tuxemon.constants import paths
import pathlib
import os
import json
import zipfile

class Manager:

    def __init__(self, url="http://127.0.0.1:5000", caching=False):
        packages_path = os.path.join(paths.CACHE_DIR, "packages")

        self.url = url

        if caching:
            if pathlib.Path(packages_path).exists():
                with open(packages_path) as file:
                    self.packages = json.loads(file.read())
            else:
                self.packages = self.update()
                """with urllib.request.urlopen(url + "/api/packages") as packages:
                    self.packages = json.loads(packages.read().decode("UTF-8"))"""

                with open(packages_path, "w") as file:
                    file.write(json.dumps(self.packages, indent=4))
        else:
            self.packages = self.update()

    def update(self):
        """Returns the response from the server"""
        with urllib.request.urlopen(self.url + "/api/packages") as packages:
            return json.loads(packages.read().decode("UTF-8"))

    def list_packages(self):
        """Returns package dictionary, either from the server or the cache"""
        return self.packages

    def download_package(self, author, name, release, dont_extract=False):
        """Downloads the specified package"""
        url = self.url + f"/packages/{author.lower()}/{name}/releases/{release}/download"
        filename = os.path.join(paths.CACHE_DIR + f"/{author}.{name}.{release}.zip")
        
        urllib.request.urlretrieve(url, filename=filename)


        outfolder = os.path.join(paths.BASEDIR, "mods", f"{name}-{author.lower()}")
        if not dont_extract:
            self.extract(filename, outfolder) 
            # Adding author name to prevent conflicts,
            # They will be resolved server side though ¯\_(ツ)_/¯
            with open(f"{outfolder}/meta.json", "w") as metafile:
                meta = self.get_package_info(author, name)
                metafile.write(json.dumps(meta, indent=4))

    def extract(self,file, outfolder):
        """Extracts the specified zip archive to the mods directory"""
        with zipfile.ZipFile(file) as zip_:
            zip_.extractall(path=os.path.join(paths.BASEDIR, "mods", outfolder))

    def get_package_info(self, author, name):
        """Get specified package info. Always downloads the info from the server."""
        with urllib.request.urlopen(self.url + f"/api/packages/{author}/{name}") as packages:
             return json.loads(packages.read().decode("UTF-8"))

    def write_package_to_list(self, path_to_folder, name):
        """Writes specified package to the package list"""
        # Write the absolute path to the list
        with open(paths.USER_GAME_DATA_DIR + "/package.list" , "w+") as file:
            if not len(file.read()) == 0:
                before = json.loads(file.read())
            else:
                before = {}

            to_append = {name: path_to_meta}
            after = {**before, **to_append}
            file.write(
                json.dumps(after, indent=4)
            )

            
