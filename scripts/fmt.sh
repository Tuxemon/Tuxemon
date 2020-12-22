#!/bin/bash

black -t py36 -l 120 tuxemon
find tuxemon/ -name "*.py" -type f | parallel pyupgrade --py36
find tuxemon/ -name "*.py" -type f | parallel autoflake -i --remove-all-unused-imports --exclude __init__
black -t py36 -l 120 tuxemon
