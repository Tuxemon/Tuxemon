#!/bin/bash

# this should be used to format and lint code
# consider using before opening a PR

pip install -U black autoflake pyupgrade
black -t py38 -l 79 tuxemon
find tuxemon/ -name "*.py" -type f | parallel pyupgrade --py38 --keep-runtime-typing
autoflake -r -i --remove-all-unused-imports --exclude "*/__init__.py" tuxemon/
black -t py38 -l 79 tuxemon
