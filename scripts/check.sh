#!/bin/bash

# Try and fix anything we can fix automatically.
# find . -name "*.py" | egrep -v '^./tests/' | grep -v './.env/' | xargs autopep8 --in-place --aggressive --aggressive --max-line-length 100 --jobs=-1 | tee autopep8.log

# Pep8 and PyFlakes
flake8 . | tee flake8.log

# Check for less obvious things.
pylint --output-format=parseable --reports=y core | tee pylint.log
