#!/bin/bash
find mods -name "*.png" | parallel -j$(nproc) --progress -q advpng -4 -i100 -q -z
