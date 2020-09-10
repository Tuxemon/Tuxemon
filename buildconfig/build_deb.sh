#!/bin/bash
export PYBUILD_DISABLE=test
cd tuxemon-*
cp ../dist/* ..
debmake -b':py3'
echo "./mods usr/share/tuxemon/"
dpkg-buildpackage -us -uc
cd ..
mv tuxemon*.deb build/tuxemon-$TRAVIS_BRANCH.deb
