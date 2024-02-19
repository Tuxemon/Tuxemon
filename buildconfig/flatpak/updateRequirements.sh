TAG="development" # branch or tag
mkdir -p build
wget -P build https://raw.githubusercontent.com/flatpak/flatpak-builder-tools/master/pip/flatpak-pip-generator
wget -P build https://raw.githubusercontent.com/Tuxemon/Tuxemon/$TAG/requirements.txt
python3 build/flatpak-pip-generator --requirements-file=build/requirements.txt