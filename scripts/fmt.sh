#!/bin/bash

# this should be used to format and lint code
# consider using before opening a PR

pip install -U black autoflake pyupgrade
black -t py36 -l 120 tuxemon
find tuxemon/ -name "*.py" -type f | parallel pyupgrade --py36
autoflake -r -i --remove-all-unused-imports --exclude "*/__init__.py" tuxemon/
black -t py36 -l 120 tuxemon
