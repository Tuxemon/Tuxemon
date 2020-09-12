#!/bin/bash
pip install git+https://github.com/pygame/python-for-android.git
p4a --version
# python buildconfig/build_android.py
p4a apk
  --name Tuxemon \
  --private tusemon \
  --version 0.0 \
  --package=org.tuxemon.Tuxemon \
  --requirements=python3,pygame