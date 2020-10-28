#!/bin/bash
find mods -name "*png" | parallel --progress -q optipng -silent -o7
