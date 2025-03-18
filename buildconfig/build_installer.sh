#!/bin/bash
NSIS_DOWNLOAD_LINK="https://sourceforge.net/projects/nsis/files/NSIS%203/3.10/nsis-3.10-setup.exe"
NSIS_INSTALLER="nsis.exe"
INSTALLER_OUTPUT="tuxemon-installer.exe"
DIST_DIR="../dist"

# Install wget
sudo apt -y install wget

# Download NSIS
wget "$NSIS_DOWNLOAD_LINK" -O "$NSIS_INSTALLER"
if [ $? -ne 0 ]; then
  echo "Error: Failed to download NSIS installer."
  exit 1
fi

# Install NSIS with Wine
wine "$NSIS_INSTALLER" /S
if [ $? -ne 0 ]; then
  echo "Error: Failed to install NSIS."
  exit 1
fi

# Run the build script
wine cmd /c "build_installer.bat"
if [ $? -ne 0 ]; then
  echo "Error: build_installer.bat failed."
  exit 1
fi

# Create the dist directory
mkdir -p "$DIST_DIR"

# Move the installer
if [ -f "$INSTALLER_OUTPUT" ]; then
    mv "$INSTALLER_OUTPUT" "$DIST_DIR"
else
    echo "Error: Installer output not found."
    exit 1
fi

echo "Installer build complete."

exit 0
