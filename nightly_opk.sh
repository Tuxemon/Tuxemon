#!/bin/sh
sudo apt-get --assume-yes install git curl squashfs-tools
sed -i 's/resolution_x.*/resolution_x = 320/g' tuxemon/tuxemon.cfg
sed -i 's/resolution_y.*/resolution_y = 240/g' tuxemon/tuxemon.cfg
sed -i 's/fullscreen.*/fullscreen = 1/g' tuxemon/tuxemon.cfg
cp tuxemon/resources/gfx/icon_32.png tuxemon/resources/gfx/icon.png
mksquashfs tuxemon tuxemon-unstable-latest.opk -all-root -noappend -no-exports -no-xattrs
