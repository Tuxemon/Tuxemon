#!/bin/bash

# Run Ruff linting
ruff check tuxemon tests | tee ruff.log

# Run Ruff formatting check (optional, but recommended)
ruff format --check tuxemon tests | tee ruff-format.log

# Run Pylint for deeper static analysis
pylint --output-format=parseable --reports=y tuxemon | tee pylint.log
