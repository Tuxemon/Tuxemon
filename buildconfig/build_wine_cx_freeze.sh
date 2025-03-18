#!/bin/bash
# debian 10 & ubuntu focal
PYTHON_VERSION="3.9"
WINE_PYTHON="wine python${PYTHON_VERSION}"
BUILD_DIR="build/exe.win*"
DIST_DIR="dist/windows_cx_freeze"

# Install dependencies
$WINE_PYTHON -m pip install -U setuptools wheel cx_Freeze
if [ $? -ne 0 ]; then
  echo "Error: Failed to install cx_Freeze dependencies."
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

# Build with cx_Freeze
$WINE_PYTHON buildconfig/setup_cx_freeze.py build
if [ $? -ne 0 ]; then
  echo "Error: cx_Freeze build failed."
  exit 1
fi

# Copy necessary files
BUILD_PATH=$(find build -name "exe.win*" | head -n 1)

if [ -z "$BUILD_PATH" ]; then
    echo "Error: Build directory not found."
    exit 1
fi

cd "$BUILD_PATH"

cp ~/.wine/drive_c/Program\ Files/Python${PYTHON_VERSION}/python${PYTHON_VERSION}.dll .
if [ $? -ne 0 ]; then
  echo "Error: Failed to copy python DLL."
  exit 1
fi

cp ../../LICENSE .
cp ../../CONTRIBUTING.md .
cp ../../CONTRIBUTORS.md .
cp ../../ATTRIBUTIONS.md .
cp ../../README.md .
cp ../../SPYDER_README.md .
cd ../../

# Create dist directory
mkdir -p "$DIST_DIR"

# Copy build output to dist
cp -a "$BUILD_PATH"/* "$DIST_DIR"
if [ $? -ne 0 ]; then
  echo "Error: Failed to copy build output to dist."
  exit 1
fi

echo "Windows cx_Freeze build complete."

exit 0
