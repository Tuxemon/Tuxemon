#!/bin/bash

###############  NOTICE  ################
# Tested with a debian bookworm container
# Depends on coreutils, curl and tar

download () {
  command curl -L -o $1 $2
}

root_folder="$(dirname $(readlink -f $0))/../"
pypy_vers="pypy3.9"
pypy_build="pypy3.9-v7.3.13-linux64"
pypy_archive="$pypy_build.tar.bz2"

if [[ -e build/pypy-linux-64bit ]]; then rm -rf build/pypy-linux-64bit; fi
mkdir -p build/pypy-linux-64bit
cd build

if ! [[ -e pypy_archive ]]; then
  download $pypy_archive "https://downloads.python.org/pypy/$pypy_archive"
fi

cd pypy-linux-64bit
tar -xf ../$pypy_archive
mv $pypy_build pypy

cp -a $root_folder/tuxemon pypy/lib/$pypy_vers/tuxemon
cp -a $root_folder/mods .
pypy/bin/pypy -m ensurepip
pypy/bin/pypy -m pip install pygame-ce==2.2.0
pypy/bin/pypy -m pip install -r "$root_folder/requirements.txt"
cp $root_folder/LICENSE .
cp $root_folder/run_tuxemon.py .
cp $root_folder/CONTRIBUTING.md .
cp $root_folder/CONTRIBUTORS.md .
cp $root_folder/ATTRIBUTIONS.md .
cp $root_folder/README.md .
cp $root_folder/SPYDER_README.md .
find . -name "*pyc" -delete

cat << EOF >> Tuxemon.sh
#!/bin/bash
FWD=\$(dirname \$(readlink -f \$0))
\$FWD/pypy/bin/pypy \$FWD/run_tuxemon.py
EOF

chmod a+x Tuxemon.sh

