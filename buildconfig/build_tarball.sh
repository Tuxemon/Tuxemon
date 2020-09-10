#!/bin/bash
pip install -U setuptools
pip install -r requirements.txt
mkdir -p ./build
python setup.py sdist
