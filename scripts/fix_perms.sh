#!/bin/bash
FOLDERS=("buildconfig" "docs" "mods" "scripts" "tests" "tuxemon")

for folder in "${FOLDERS[@]}"
do
	find "$folder" -type f -print0 | parallel -q0 chmod 0644
	find "$folder" -type d -print0 | parallel -q0 chmod 0755
done
chmod 0744 buildconfig/*sh
chmod 0744 scripts/*sh
chmod +x tuxemon.py
