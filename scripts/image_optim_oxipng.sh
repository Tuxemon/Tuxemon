#!/bin/bash
find mods -name "*png" | parallel --progress -q oxipng -q --strip safe -o max -Z --nx - 
 
