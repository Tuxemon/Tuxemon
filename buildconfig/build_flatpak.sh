#!/bin/bash
buildconfig/build_tarball.sh
flatpak-builder build buildconfig/flatpak/tuxemon.yaml
