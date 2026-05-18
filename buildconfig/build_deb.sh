#!/bin/bash
set -e
export PYBUILD_DISABLE=test
python3 -m build --sdist
cd dist
tar -xf tuxemon-*.tar.gz
cd tuxemon-*
cp ../tuxemon-*.tar.gz ..
debmake -b':py3'
echo "./mods usr/share/tuxemon/" > debian/install
dpkg-buildpackage -us -uc -b
cd ..
version=$(python3 -c "import tuxemon; print(tuxemon.__version__)")
branch=$(git rev-parse --abbrev-ref HEAD)
date=$(date +%Y%m%d)
mkdir -p build
mv tuxemon*.deb build/tuxemon-${version}-${branch}-${date}.deb
