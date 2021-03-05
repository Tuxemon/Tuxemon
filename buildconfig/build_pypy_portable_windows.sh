#!/bin/bash
# currently needs a compiler to build pygame.  needs to be tested on windows.
build_folder="tuxemon"
pypy_build="pypy3.7-v7.3.3-win32"
pypy_archive="$pypy_build.zip"
mkdir -p build/pypy-win32
cd build/pypy-win32
[ -e $pypy_archive ] || wget -q https://downloads.python.org/pypy/$pypy_archive
[ -e $build_folder ] || {
 unzip $pypy_archive
 mv $pypy_build $build_folder
}
cd $build_folder
cp -a ../../../tuxemon site-packages/
cp -a ../../../mods .
wine pypy3.exe -m ensurepip
wine pypy3.exe -m pip install -r ../../../requirements.txt
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
[ -e run_tuxemon.bat ] || {
 cat > run_tuxemon.bat << EOF
pypy3.exe run_tuxemon.py
EOF
 chmod +x run_tuxemon.sh
}
[ -e README_WINDOWS.txt ] || {
 cat > README_WINDOWS.txt << EOF
If the game does not start, you may need the following to be installed:
https://www.microsoft.com/en-us/download/details.aspx?id=52685
EOF
}
