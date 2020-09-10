#!/bin/bash
pip install -r requirements.txt
mkdir -p ./build
python setup.py sdist --keep-temp
