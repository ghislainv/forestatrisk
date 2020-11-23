#!/bin/bash

set -ex

svg=$1

size=(16 24 32 48 57 64 76 96 120 128 144 152 180 195 196 228 270)

out="$(mktemp -d)"

echo Making bitmaps from your svg...

for i in ${size[@]}; do
  inkscape $svg --export-filename="$out/$i.png" -w $i -h $i
done

echo Compressing...

## Replace with your favorite (e.g. pngquant)
for i in ${size[@]}; do
    optipng -o7 "$out/$i.png"
done
#pngquant -f --ext .png "$out/*.png" --posterize 4 --speed 1

echo Converting to favicon.ico...

convert "$out/*.png" favicon.ico

# Clean-up
rm -rf "$out/"

echo Done

# EOF
