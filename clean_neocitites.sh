#!/bin/bash

#
# clean_neocities - script for removing anything that's not in the local version of the site.
#
# Usage: ./clean_neocities.sh path/to/built/site/
# (e.g., ./clean_neocities.sh build/site/ )

echo "!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  !!"
echo "!!                                                                    !!"
echo "!!   If your res/ folder is not up to date, everything newer on the   !!"
echo "!!   server WILL be deleted!! Double check if anything's missing!!!   !!"
echo "!!                                                                    !!"
echo "!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  CAUTION!!  !!"
echo
echo "Script will start in..."
echo "3"
sleep 1
echo "2"
sleep 1
echo "1"
sleep 1
echo "Cleaning site..."
mkdir tmp
cd tmp
neocities pull
# This probably also works on linux but i can't be bothered
# to actually check rn, at least the other one has been tested :P
if [[ "$OSTYPE" == "darwin"* ]]; then
    neocities delete $(diff -q -r . ../$1 \
        | grep -E "Only in .:|Only in ./"\
        | sed -E "s/Only in .([^:]*): (.+)/\1\/\2 /"\
        | cut -c 2-\
        | tr -d '\n')
else
    neocities delete $(diff -q -r . ../$1 \
        | grep -E "Only in .:|Only in ./"\
        | sed -r "s/Only in .(.+?): (.+)/\1\/\2 /"\
        | cut -c 2-\
        | tr -d '\n')
fi
cd ..
rm -r tmp