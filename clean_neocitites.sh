#!/bin/bash

#
# clean_neocities - script for removing anything that's not in the local version of the site.
#
# Usage: ./clean_neocities.sh path/to/built/site/
# (e.g., ./clean_neocities.sh build/site/ )

mkdir tmp
cd tmp
neocities pull
neocities delete $(diff -q -r . ../$1 \
    | grep -E "Only in .:|Only in ./"\
    | sed -r "s/Only in .(.+?): (.+)/\1\/\2 /"\
    | cut -c 2-\
    | tr -d '\n')
cd ..
rm -r tmp