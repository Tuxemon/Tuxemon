#!/usr/bin/env python3

import fnmatch
import os

from setuptools import setup, find_packages
from setuptools.command.install import install


def build_translations():
    from tuxemon.core.locale import T

    T.collect_languages()


class InstallAndBuildTranslations(install):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # build_translations()


# Get the version from the README file.
with open("README.md", "r") as f:
    VERSION = f.readline().split(" ")[-1].replace("\n", "")

# Get the dependencies from requirements.text
with open("requirements.txt", "r") as f:
    REQUIREMENTS = f.read().splitlines()

# Configure the setuptools    
setup(
    name='tuxemon',
    version='1.0',
    author='Meir Woda',
    author_email='meir.woda@gmail.com',
    packages=find_packages(),

)
