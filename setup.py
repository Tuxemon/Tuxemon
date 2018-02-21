#!/usr/bin/env python

from setuptools import setup
import fnmatch
import os

# Find all the python modules
modules = []
matches = []
for root, dirnames, filenames in os.walk('tuxemon'):
    for filename in fnmatch.filter(filenames, '__init__.py'):
        matches.append(os.path.join(root, filename))

for match in matches:
    match = match.replace(os.sep+"__init__.py", "")
    match = match.replace(os.sep, ".")
    modules.append(match)

# Get the version from the README file.
f = open("README.md", "r")
VERSION = f.readline().split(" ")[-1].replace("\n", "")
f.close()

# Configure the setuptools
setup(name='Tuxemon',
      version=VERSION,
      description='Open source monster-fighting RPG',
      author='William Edwards',
      author_email='shadowapex@gmail.com',
      url='https://www.tuxemon.org',
      include_package_data=True,
      packages=modules,
      entry_points={
          'gui_scripts': [
              'tuxemon = tuxemon.__main__:main'
          ]
      },
      )
