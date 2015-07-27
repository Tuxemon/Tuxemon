#!/bin/bash

set -e
set -x

#sudo apt-get install python-pygame python-imaging python-yapsy
pip install hg+http://bitbucket.org/pygame/pygame
pip install pytmx Pillow Yapsy
