#!/bin/bash
sudo apt-get update
sudo apt-get install -y flatpak-builder
flatpak-builder build buildconfig/flatpak/tuxemon.yaml
