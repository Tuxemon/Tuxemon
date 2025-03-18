#!/bin/bash

###############  NOTICE  ################
# Tested with a debian bookworm container
# Depends on coreutils, curl and tar
PYPY_VERSION="pypy3.9"
PYPY_BUILD="pypy3.9-v7.3.13-linux64"
PYGAME_VERSION="2.2.0"
ROOT_FOLDER="$(dirname "$(readlink -f "$0")")/../"
BUILD_DIR="build/pypy-linux-64bit"
PYPY_ARCHIVE="$PYPY_BUILD.tar.bz2"

# Dependency Check
command -v curl >/dev/null 2>&1 || { echo >&2 "curl is required but not installed. Aborting."; exit 1; }
command -v tar >/dev/null 2>&1 || { echo >&2 "tar is required but not installed. Aborting."; exit 1; }

# Download function with error handling
download () {
  curl -L -o "$1" "$2"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to download $1 from $2"
    exit 1
  fi
}

# Clean and create build directory
if [[ -e "$BUILD_DIR" ]]; then
  rm -rf "$BUILD_DIR"
fi
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Download PyPy archive
if ! [[ -e "$PYPY_ARCHIVE" ]]; then
  download "$PYPY_ARCHIVE" "https://downloads.python.org/pypy/$PYPY_ARCHIVE"
fi

# Extract PyPy archive
tar -xf "../$PYPY_ARCHIVE"
if [ $? -ne 0 ]; then
  echo "Error: Failed to extract $PYPY_ARCHIVE"
  exit 1
fi
mv "$PYPY_BUILD" pypy

# Copy project files
cp -a "$ROOT_FOLDER/tuxemon" "pypy/lib/$PYPY_VERSION/tuxemon"
cp -a "$ROOT_FOLDER/mods" .

# Install dependencies with PyPy
pypy/bin/pypy -m ensurepip
if [ $? -ne 0 ]; then
  echo "Error: ensurepip failed."
  exit 1
fi

pypy/bin/pypy -m pip install "pygame-ce==$PYGAME_VERSION"
if [ $? -ne 0 ]; then
  echo "Error: Failed to install pygame-ce."
  exit 1
fi

pypy/bin/pypy -m pip install -r "$ROOT_FOLDER/requirements.txt"
if [ $? -ne 0 ]; then
  echo "Error: Failed to install requirements."
  exit 1
fi

cp "$ROOT_FOLDER/LICENSE" .
cp "$ROOT_FOLDER/run_tuxemon.py" .
cp "$ROOT_FOLDER/CONTRIBUTING.md" .
cp "$ROOT_FOLDER/CONTRIBUTORS.md" .
cp "$ROOT_FOLDER/ATTRIBUTIONS.md" .
cp "$ROOT_FOLDER/README.md" .
cp "$ROOT_FOLDER/SPYDER_README.md" .

# Clean up .pyc files
find . -name "*.pyc" -delete
if [ $? -ne 0 ]; then
  echo "Error: Failed to delete .pyc files."
  exit 1
fi

# Create Tuxemon.sh
cat << EOF > Tuxemon.sh
#!/bin/bash
FWD=\$(dirname \$(readlink -f \$0))
\$FWD/pypy/bin/pypy \$FWD/run_tuxemon.py
EOF

chmod a+x Tuxemon.sh

echo "Linux PyPy build complete."

exit 0
