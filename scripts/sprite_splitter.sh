#!/bin/bash
#
# Sprite Splitter
# Copyright (C) 2013, William Edwards <shadowapex@gmail.com>
#
# This file is part of Sprite Splitter.
#
# Sprite Splitter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sprite Splitter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sprite Splitter.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# sprite_splitter.sh Sprite splitting utility
#
# Sprite Splitter is used to convert a single sprite sheet image into
# multiple individual images for each tile.
#
# Usage:
# ./sprite_splitter.sh <tile_width> <tile_height> <file>
#
#

# Check to see if ImageMagick is installed
OUTPUT=`which convert`
EXITCODE=`echo $?`

if [[ "$EXITCODE" == "1" ]]; then
	echo "ImageMagick not found."
	exit 1
fi

# Check if identify is installed
OUTPUT=`which identify`
EXITCODE=`echo $?`

if [[ "$EXITCODE" == "1" ]]; then
	echo "ImageMagick not found."
	exit 1
fi

# Check to see if the correct number of arguments were passed
if [[ "$#" == "3" ]]; then
	TILE_WIDTH=$1
	TILE_HEIGHT=$2
	FILENAME=$3
elif [[ "$#" == "0" ]]; then
	echo "Please enter the width in pixels to crop:"
	read TILE_WIDTH

	echo "Please enter the height in pixels to crop:"
	read TILE_HEIGHT

	echo "Please enter the file to crop:"
	read FILENAME
else
	echo "Usage: ./sprite_splitter.sh <tile_width> <tile_height> <file>"
	exit 1
fi


# Get the image dimensions
IMAGE_SIZE=`identify $FILENAME | awk {'print $3'}`

# Split the dimensions into height and width
IMAGE_WIDTH=`echo $IMAGE_SIZE | cut -d'x' -f 1`
IMAGE_HEIGHT=`echo $IMAGE_SIZE | cut -d'x' -f 2`

# Set the offset variables so we can crop each subsequent tile
OFFSET_X=0
OFFSET_Y=0

COLUMNS=$(($IMAGE_WIDTH/$TILE_WIDTH))
ROWS=$(($IMAGE_HEIGHT/$TILE_HEIGHT))

current_row=0
current_column=0

# Loop through each column in the image
while [[ $current_row -lt $ROWS ]]; do

        # Reset the x value back to 0 for each row
        OFFSET_X=0
	current_column=0

        while [[ $current_column -lt $COLUMNS ]]; do
		echo "convert -extract ${TILE_WIDTH}x${TILE_HEIGHT}+${OFFSET_X}+${OFFSET_Y} ${FILENAME} ${current_column}x${current_row}-${FILENAME}"
		convert -extract ${TILE_WIDTH}x${TILE_HEIGHT}+${OFFSET_X}+${OFFSET_Y} ${FILENAME} ${current_column}x${current_row}-${FILENAME}
                current_column=$(($current_column+1))
                OFFSET_X=$(($OFFSET_X+$TILE_WIDTH))
	done

        current_row=$(($current_row+1))
        OFFSET_Y=$((${OFFSET_Y}+${TILE_HEIGHT}))
done


exit 0
