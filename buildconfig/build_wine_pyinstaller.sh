#!/bin/bash
# debian 10
PYTHON_VERSION="3.9"
WINE_PYTHON="wine python${PYTHON_VERSION}"
BUILD_DIR="build/tuxemon"

# Run setup script
buildconfig/setup_wine_debian10.sh
if [ $? -ne 0 ]; then
  echo "Error: setup_wine_debian10.sh failed."
  exit 1
fi

# Install dependencies
$WINE_PYTHON -m pip install -U setuptools wheel pyinstaller
if [ $? -ne 0 ]; then
  echo "Error: Failed to install PyInstaller dependencies."
  exit 1
fi

$WINE_PYTHON -m pip install -U -r requirements.txt
if [ $? -ne 0 ]; then
  echo "Error: Failed to install project dependencies."
  exit 1
fi

# Clean up .pyc files
find . -name "*.pyc" -delete
if [ $? -ne 0 ]; then
  echo "Error: Failed to delete .pyc files."
  exit 1
fi

# Build with PyInstaller
wine pyinstaller buildconfig/pyinstaller/tuxemon.spec
if [ $? -ne 0 ]; then
  echo "Error: PyInstaller build failed."
  exit 1
fi

# Copy necessary files
if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: Build directory not found."
    exit 1
fi

cd "$BUILD_DIR"

cp ~/.wine/drive_c/Program\ Files/Python${PYTHON_VERSION}/python${PYTHON_VERSION}.dll .
if [ $? -ne 0 ]; then
  echo "Error: Failed to copy python DLL."
  exit 1
fi

cd ../../

cp LICENSE "$BUILD_DIR"
cp CONTRIBUTING.md "$BUILD_DIR"
cp CONTRIBUTORS.md "$BUILD_DIR"
cp ATTRIBUTIONS.md "$BUILD_DIR"
cp README.md "$BUILD_DIR"
cp SPYDER_README.md "$BUILD_DIR"

echo "Windows PyInstaller build complete."

exit 0
