#!/usr/bin/env python3

import fnmatch
import os

from setuptools import setup
from setuptools.command.install import install


def build_translations():
    from tuxemon.core.locale import T

    T.collect_languages()

class InstallAndBuildTranslations(install):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        build_translations()


# Find all the python modules
modules = []
matches = []
for root, dirnames, filenames in os.walk('tuxemon'):
    for filename in fnmatch.filter(filenames, '__init__.py'):
        matches.append(os.path.join(root, filename))

for match in matches:
    match = match.replace(os.sep + "__init__.py", "")
    match = match.replace(os.sep, ".")
    modules.append(match)

# Get the version from the README file.
with open("README.md", "r") as f:
    VERSION = f.readline().split(" ")[-1].replace("\n", "")

# Get the dependencies from requirements.text
with open("requirements.txt", "r") as f:
    REQUIREMENTS = f.read().splitlines()

# Configure the setuptools
setup(name='tuxemon',
      version=VERSION,
      description='Open source monster-fighting RPG',
      author='William Edwards',
      author_email='shadowapex@gmail.com',
      maintainer='Tuxemon',
      maintainer_email='info@tuxemon.org',
      url='https://www.tuxemon.org',
      include_package_data=True,
      packages=modules,
      license="GPLv3",
      long_description='https://github.com/Tuxemon/Tuxemon',
      install_requires=REQUIREMENTS,
      python_requires='>=3.3',
      entry_points={
          'gui_scripts': [
              'tuxemon = tuxemon.__main__:main'
          ]
      },
      classifiers=[
          "Intended Audience :: End Users/Desktop",
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Topic :: Games/Entertainment",
          "Topic :: Games/Entertainment :: Role-Playing",
      ],
      cmdclass={'install': InstallAndBuildTranslations}
      )
