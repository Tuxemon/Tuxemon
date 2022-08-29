#!/bin/bash

# this should be used to format and lint code
# consider using before opening a PR

pip install -U black autoflake pyupgrade isort
find tuxemon/ -name "*.py" -type f | parallel pyupgrade --py38-plus --keep-runtime-typing
autoflake -r -i --imports=tuxemon,pygame --ignore-init-module-imports tuxemon/
isort black tuxemon tests
black tuxemon tests
