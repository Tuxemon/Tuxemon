#!/bin/bash
# Notice this requires advpng from https://github.com/amadvance/advancecomp
# You will most likely need to compile it and install it
find mods -name "*.png" | parallel -j$(nproc) --progress -q advpng -4 -i100 -q -z && find mods -name "*.png" | parallel -j$(nproc) --progress -q advpng -4 -i100 -q -z
