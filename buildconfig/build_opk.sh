#!/bin/bash
sudo apt-get update
sudo apt-get install -y squashfs-tools
mksquashfs tuxemon ./build/tuxemon-unstable-latest.opk -all-root -noappend -no-exports -no-xattrs
