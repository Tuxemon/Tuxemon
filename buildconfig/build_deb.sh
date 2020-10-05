#!/bin/bash
export PYBUILD_DISABLE=test
python setup.py sdist --keep-temp
cd tuxemon-*
cp ../dist/* ..
debmake -b':py3'
echo "./mods usr/share/tuxemon/" > debian/install
dpkg-buildpackage -us -uc -b
cd ..
mv tuxemon*.deb build/tuxemon-$TRAVIS_DIST-$TRAVIS_BRANCH.deb
