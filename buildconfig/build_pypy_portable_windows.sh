#!/bin/bash

###############  NOTICE  ################
# Tested with a debian bookworm container
# Depends on coreutils, curl, p7zip-full and wine

download () {
  command curl -L -o $1 $2
}

root_folder="$(dirname $(readlink -f $0))/../"
pypy_vers="pypy3.9"
pypy_build="pypy3.9-v7.3.13-win64"
pypy_archive="$pypy_build.zip"

if [[ -e build/pypy-win-64bit ]]; then rm -rf build/pypy-win-64bit; fi
mkdir -p build/pypy-win-64bit
cd build/

if ! [[ -e $pypy_archive ]]; then
  download $pypy_archive https://downloads.python.org/pypy/$pypy_archive
fi

cd pypy-win-64bit

7z x ../$pypy_archive
mv $pypy_build pypy

wine64 pypy/pypy.exe -m ensurepip
wine64 pypy/pypy.exe -m pip install pygame-ce==2.2.0
wine64 pypy/pypy.exe -m pip install -r "$root_folder/requirements.txt"
cp -a $root_folder/tuxemon pypy/Lib/tuxemon
cp -a $root_folder/mods .
cp $root_folder/LICENSE .
cp $root_folder/run_tuxemon.py .
cp $root_folder/CONTRIBUTING.md .
cp $root_folder/CONTRIBUTORS.md .
cp $root_folder/ATTRIBUTIONS.md .
cp $root_folder/README.md .
cp $root_folder/SPYDER_README.md .
find . -name "*pyc" -delete

cat << EOF >> Tuxemon.bat
SETCONSOLE /Hide
%~dp0\\pypy\\bin\\pypy.exe %~dp0\\run_tuxemon.py
EOF
chmod a+x Tuxemon.bat

cat << EOF >> README_WINDOWS.txt
If the game does not start you may need to install vcredist:
https://www.microsoft.com/en-us/download/details.aspx?id=52685
EOF

