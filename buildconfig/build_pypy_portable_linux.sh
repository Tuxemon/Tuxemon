#!/bin/bash
build_folder="tuxemon"
pypy_build="pypy3.7-v7.3.3-linux64"
pypy_archive="$pypy_build.tar.bz2"
mkdir -p build/pypy-linux64
cd build/pypy-linux64
[ -e $pypy_archive ] || wget -q https://downloads.python.org/pypy/$pypy_archive
[ -e $build_folder ] || {
 tar xf $pypy_archive
 mv $pypy_build $build_folder
}
cd $build_folder
cp -a ../../../tuxemon site-packages/
cp -a ../../../mods .
bin/pypy3.7 -m ensurepip
bin/pypy3.7 -m pip install -r ../../../requirements.txt
[ -e docs ] || mkdir docs
[ -e README.rst ] && mv README.rst docs
[ -e LICENSE ] && mv LICENSE docs/PYPY_LICENSE
cp ../../../LICENSE docs/TUXEMON_LICENSE
cp ../../../run_tuxemon.py .
cp ../../../CONTRIBUTING.md .
cp ../../../CREDITS.md .
cp ../../../README.md .
cp ../../../SPYDER_README.md .
find . -name "*pyc" -delete
[ -e run_tuxemon.sh ] || {
 cat > run_tuxemon.sh << EOF
#!/bin/bash
bin/pypy3 run_tuxemon.py
EOF
 chmod +x run_tuxemon.sh
}
